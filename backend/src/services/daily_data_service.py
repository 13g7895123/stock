"""Daily stock data scraping service."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)


class DailyDataService:
    """Service for fetching and managing daily stock data from broker websites."""
    
    def __init__(self, db_session: Session = None):
        """Initialize the daily data service."""
        self.db_session = db_session
        self.timeout = httpx.Timeout(30.0)
        self.broker_urls = [
            "http://fubon-ebrokerdj.fbs.com.tw/",
            "http://justdata.moneydj.com/",
            "http://jdata.yuanta.com.tw/",
            "http://moneydj.emega.com.tw/",
            "http://djfubonholdingfund.fbs.com.tw/",
            "https://sjmain.esunsec.com.tw/",
            "http://kgieworld.moneydj.com/",
            "http://newjust.masterlink.com.tw/"
        ]
    
    def validate_daily_data(self, data: Dict[str, Any]) -> bool:
        """Simplified validation for daily stock data - accept raw broker data as is."""
        required_fields = [
            "stock_code", "trade_date", "open_price", "high_price", 
            "low_price", "close_price", "volume"
        ]
        
        # Check required fields exist
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
        
        # Basic type and positive value checks only - no strict validation
        price_fields = ["open_price", "high_price", "low_price", "close_price"]
        for field in price_fields:
            price = data[field]
            if not isinstance(price, (int, float)) or price <= 0:
                return False
        
        # Volume must be non-negative
        volume = data["volume"]
        if not isinstance(volume, int) or volume < 0:
            return False
        
        # Accept all data that passes basic checks - no price relationship validation
        return True
    
    def is_stock_data_up_to_date(self, stock_id: str) -> bool:
        """Check if stock data is up to date (within last 3 days to account for weekends)."""
        try:
            latest_date = self.get_latest_date_from_database(stock_id)
            if not latest_date:
                return False
            
            # Convert to date if it's datetime
            if isinstance(latest_date, datetime):
                latest_date = latest_date.date()
            
            # Check if the latest data is within reasonable time range
            today = date.today()
            days_diff = (today - latest_date).days
            
            # Consider up-to-date if data is from last 7 days 
            # This accounts for weekends and holidays when there's no trading
            # 7 days should cover most weekend and holiday scenarios
            is_recent = days_diff <= 7
            
            if is_recent:
                logger.info(f"Stock {stock_id} data is up to date (latest: {latest_date}, {days_diff} days ago)")
            else:
                logger.info(f"Stock {stock_id} data needs update (latest: {latest_date}, {days_diff} days ago)")
                
            return is_recent
            
        except Exception as e:
            logger.error(f"Error checking if stock {stock_id} data is up to date: {e}")
            return False
    
    def build_broker_url(self, base_url: str, stock_id: str) -> str:
        """Build the complete broker URL with stock parameters."""
        # Remove trailing slash and add the specific path
        base_url = base_url.rstrip('/')
        path = f"/z/BCD/czkc1.djbcd?a={stock_id}&b=A&c=2880&E=1&ver=5"
        return f"{base_url}{path}"
    
    def parse_broker_response(self, response_text: str, stock_id: str) -> List[Dict[str, Any]]:
        """Parse broker response text into structured daily data.
        
        Broker format: dates1,date2,...,dateN,open1,open2,...,openN,high1,high2,...,highN,low1,low2,...,lowN,close1,close2,...,closeN,volume1,volume2,...,volumeN
        Where dates are in YYYY/MM/DD format and price data is grouped by type (all opens, all highs, all lows, all closes, all volumes).
        """
        daily_data = []
        
        try:
            parts = response_text.split(',')
            logger.info(f"Total parts in broker response: {len(parts)}")
            
            # Step 1: Separate dates from numeric values
            dates = []
            all_numbers = []
            
            for part in parts:
                part = part.strip()
                
                # Check if this part is a date (YYYY/MM/DD format)
                if '/' in part and len(part.split('/')) == 3:
                    try:
                        # Validate date format
                        year, month, day = part.split('/')
                        if len(year) == 4 and len(month) <= 2 and len(day) <= 2:
                            if 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                                dates.append(part)
                                continue
                    except ValueError:
                        pass
                
                # Check if this part is a pure number
                try:
                    number = float(part)
                    all_numbers.append(number)
                except ValueError:
                    # Handle mixed formats like "date price" or "volume price"
                    if ' ' in part:
                        space_parts = part.split()
                        for space_part in space_parts:
                            # Check if it's a date
                            if '/' in space_part and len(space_part.split('/')) == 3:
                                try:
                                    year, month, day = space_part.split('/')
                                    if len(year) == 4 and 1900 <= int(year) <= 2100:
                                        dates.append(space_part)
                                        continue
                                except ValueError:
                                    pass
                            # Otherwise try to parse as number
                            try:
                                number = float(space_part)
                                all_numbers.append(number)
                            except ValueError:
                                pass
            
            logger.info(f"Parsed {len(dates)} dates and {len(all_numbers)} numbers for {stock_id}")
            
            if len(dates) == 0 or len(all_numbers) == 0:
                logger.warning("No valid dates or numbers found in broker response")
                return []
            
            # Step 2: Map dates to OHLCV data using correct broker format
            # Broker data structure: all_opens, all_highs, all_lows, all_closes, all_volumes
            num_dates = len(dates)
            logger.info(f"Processing {num_dates} dates with {len(all_numbers)} numbers")
            
            if len(all_numbers) < num_dates * 4:  # Need at least OHLC data
                logger.warning(f"Insufficient data: need at least {num_dates * 4} numbers for OHLC, got {len(all_numbers)}")
                return []
            
            # Extract data sections based on broker structure
            opens = all_numbers[0:num_dates] if len(all_numbers) >= num_dates else []
            highs = all_numbers[num_dates:num_dates*2] if len(all_numbers) >= num_dates*2 else []
            lows = all_numbers[num_dates*2:num_dates*3] if len(all_numbers) >= num_dates*3 else []
            closes = all_numbers[num_dates*3:num_dates*4] if len(all_numbers) >= num_dates*4 else []
            volumes = all_numbers[num_dates*4:] if len(all_numbers) > num_dates*4 else []
            
            logger.info(f"Data sections - Opens: {len(opens)}, Highs: {len(highs)}, Lows: {len(lows)}, Closes: {len(closes)}, Volumes: {len(volumes)}")
            
            # Process each date with its corresponding OHLCV data
            for i in range(num_dates):
                try:
                    date_str = dates[i]
                    trade_date = datetime.strptime(date_str, '%Y/%m/%d')
                    
                    # Get OHLCV values for this date
                    if i < len(opens) and i < len(highs) and i < len(lows) and i < len(closes):
                        open_price = opens[i]
                        high_price = highs[i]
                        low_price = lows[i]
                        close_price = closes[i]
                        volume = volumes[i] if i < len(volumes) else 0
                        
                        # Validate that values are reasonable
                        if (open_price > 0 and high_price > 0 and low_price > 0 and close_price > 0 and volume >= 0):
                            data_item = {
                                "stock_code": stock_id,
                                "trade_date": trade_date,
                                "open_price": round(open_price, 4),
                                "high_price": round(high_price, 4),
                                "low_price": round(low_price, 4),
                                "close_price": round(close_price, 4),
                                "volume": int(volume)
                            }
                            
                            if self.validate_daily_data(data_item):
                                daily_data.append(data_item)
                            else:
                                logger.debug(f"Validation failed for date {date_str}: {data_item}")
                        else:
                            logger.debug(f"Invalid OHLCV values for date {date_str}: O={open_price}, H={high_price}, L={low_price}, C={close_price}, V={volume}")
                            
                except Exception as e:
                    logger.debug(f"Error parsing record {i} for date {dates[i] if i < len(dates) else 'unknown'}: {e}")
                    continue
                    
            logger.info(f"Successfully parsed {len(daily_data)} valid records out of {num_dates} possible records for {stock_id}")
            
            # Log sample data for verification
            if len(daily_data) > 0:
                sample_data = daily_data[:3] + daily_data[-2:] if len(daily_data) > 5 else daily_data
                for idx, sample in enumerate(sample_data):
                    logger.info(f"Sample {idx+1}: {sample['trade_date'].strftime('%Y-%m-%d')} - O:{sample['open_price']}, H:{sample['high_price']}, L:{sample['low_price']}, C:{sample['close_price']}, V:{sample['volume']}")
            
            # Return successfully parsed data
            logger.info(f"Final result: Parsed {len(daily_data)} records for stock {stock_id}")
            return daily_data
        
        except Exception as e:
            logger.error(f"Error parsing broker response: {e}")
            return []
        
        logger.info(f"Final result: Parsed {len(daily_data)} records for stock {stock_id}")
        return daily_data
    
    async def fetch_daily_data_from_broker(self, base_url: str, stock_id: str) -> List[Dict[str, Any]]:
        """Fetch daily data from a single broker URL."""
        try:
            url = self.build_broker_url(base_url, stock_id)
            logger.info(f"Fetching data from: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = self.parse_broker_response(response.text, stock_id)
                logger.info(f"Successfully fetched {len(data)} records from {base_url}")
                return data
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching from {base_url}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching from {base_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching from {base_url}: {e}")
            return []
    
    async def fetch_daily_data_from_all_brokers(self, stock_id: str) -> List[Dict[str, Any]]:
        """Fetch daily data from all broker URLs, return first successful result."""
        all_data = []
        
        for broker_url in self.broker_urls:
            try:
                data = await self.fetch_daily_data_from_broker(broker_url, stock_id)
                if data:
                    logger.info(f"Successfully got data from {broker_url}, found {len(data)} records")
                    all_data.extend(data)
                    break  # Use first successful broker
            except Exception as e:
                logger.warning(f"Failed to fetch from {broker_url}: {e}")
                continue
        
        if not all_data:
            raise Exception(f"Failed to fetch data from all brokers for stock {stock_id}")
        
        # Remove duplicates based on trade_date
        seen_dates = set()
        unique_data = []
        for item in all_data:
            date_key = item["trade_date"].date()
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_data.append(item)
        
        logger.info(f"Total unique records for {stock_id}: {len(unique_data)}")
        return unique_data
    
    def get_latest_date_from_database(self, stock_id: str) -> Optional[datetime]:
        """Get the latest trade date for a stock from database."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        try:
            # Import here to avoid circular imports during testing
            from src.models.stock import StockDailyData
            
            latest_record = (
                self.db_session.query(StockDailyData)
                .filter(StockDailyData.stock_code == stock_id)
                .order_by(desc(StockDailyData.trade_date))
                .first()
            )
            
            if latest_record:
                return latest_record.trade_date
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest date from database: {e}")
            return None
    
    def save_daily_data_to_database(self, daily_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Save daily data to database. Returns counts of created/updated records."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        created_count = 0
        updated_count = 0
        
        try:
            # Import here to avoid circular imports during testing
            from src.models.stock import StockDailyData
            
            for data in daily_data:
                if not self.validate_daily_data(data):
                    logger.warning(f"Skipping invalid data: {data}")
                    continue
                
                stock_code = data["stock_code"]
                trade_date = data["trade_date"]
                
                # Check if record already exists
                existing_record = (
                    self.db_session.query(StockDailyData)
                    .filter(
                        StockDailyData.stock_code == stock_code,
                        StockDailyData.trade_date == trade_date
                    )
                    .first()
                )
                
                if existing_record:
                    # Update existing record
                    existing_record.open_price = data["open_price"]
                    existing_record.high_price = data["high_price"]
                    existing_record.low_price = data["low_price"]
                    existing_record.close_price = data["close_price"]
                    existing_record.volume = data["volume"]
                    existing_record.data_source = "broker_crawler"
                    existing_record.data_quality = "corrected_daily"
                    existing_record.is_validated = True
                    updated_count += 1
                    logger.debug(f"Updated record for {stock_code} on {trade_date.date()}")
                else:
                    # Create new record
                    new_record = StockDailyData(
                        stock_code=stock_code,
                        trade_date=trade_date,
                        open_price=data["open_price"],
                        high_price=data["high_price"],
                        low_price=data["low_price"],
                        close_price=data["close_price"],
                        volume=data["volume"],
                        data_source="broker_crawler",
                        data_quality="corrected_daily",
                        is_validated=True
                    )
                    self.db_session.add(new_record)
                    created_count += 1
                    logger.debug(f"Created new record for {stock_code} on {trade_date.date()}")
            
            self.db_session.commit()
            logger.info(f"Database operation completed: {created_count} created, {updated_count} updated")
            
            return {"created": created_count, "updated": updated_count}
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving daily data to database: {e}")
            raise
    
    async def get_daily_data_for_stock(self, stock_id: str, force_update: bool = False) -> Dict[str, Any]:
        """Get daily data for a stock (main service method with intelligent skip)."""
        try:
            logger.info(f"Starting daily data fetch for stock {stock_id}")
            
            # Smart skip mechanism removed - always fetch and update data
            
            # 1. Fetch data from brokers
            daily_data = await self.fetch_daily_data_from_all_brokers(stock_id)
            
            # 2. Save to database
            save_result = self.save_daily_data_to_database(daily_data)
            
            # 3. Return success result
            result = {
                "status": "success",
                "stock_code": stock_id,
                "records_processed": len(daily_data),
                "created": save_result["created"],
                "updated": save_result["updated"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed daily data for {stock_id}: {len(daily_data)} records")
            return result
            
        except Exception as e:
            logger.error(f"Error processing daily data for {stock_id}: {e}")
            return {
                "status": "error",
                "stock_code": stock_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }