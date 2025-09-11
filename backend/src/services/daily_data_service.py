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
        """Validate daily stock data format and required fields."""
        required_fields = [
            "stock_code", "trade_date", "open_price", "high_price", 
            "low_price", "close_price", "volume"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field: {field} in daily data")
                return False
        
        # Validate stock_code format (4-digit non-zero-prefix)
        stock_code = data["stock_code"]
        if not re.match(r"^[1-9]\d{3}$", str(stock_code)):
            logger.warning(f"Invalid stock_code format: {stock_code}")
            return False
        
        # Validate trade_date is datetime or date
        trade_date = data["trade_date"]
        if not isinstance(trade_date, (datetime, date)):
            logger.warning(f"Invalid trade_date type: {type(trade_date)}")
            return False
        
        # Validate price fields are positive numbers and reasonable ranges
        price_fields = ["open_price", "high_price", "low_price", "close_price"]
        for field in price_fields:
            price = data[field]
            if not isinstance(price, (int, float)) or price <= 0:
                logger.warning(f"Invalid {field}: {price} (must be positive number)")
                return False
            # Check price is within reasonable range for Taiwan stocks (0.01 - 10000)
            if price < 0.01 or price > 10000:
                logger.warning(f"Invalid {field}: {price} (price out of reasonable range 0.01-10000)")
                return False
        
        # Validate volume is non-negative integer
        volume = data["volume"]
        if not isinstance(volume, int) or volume < 0:
            logger.warning(f"Invalid volume: {volume} (must be non-negative integer)")
            return False
        
        # Validate price relationships (high >= low, etc.)
        if data["high_price"] < data["low_price"]:
            logger.warning(f"Invalid price relationship: high ({data['high_price']}) < low ({data['low_price']})")
            return False
        
        if not (data["low_price"] <= data["open_price"] <= data["high_price"]):
            logger.warning(f"Open price ({data['open_price']}) not within high-low range")
            return False
            
        if not (data["low_price"] <= data["close_price"] <= data["high_price"]):
            logger.warning(f"Close price ({data['close_price']}) not within high-low range")
            return False
        
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
        """Parse broker response text into structured daily data."""
        daily_data = []
        
        try:
            parts = response_text.split(',')
            
            # Step 1: Extract all dates and all numeric values
            dates = []
            all_numbers = []
            
            for part in parts:
                part = part.strip()
                
                # Handle mixed date-price format like "2025/09/09 258.2756"
                if '/' in part and ' ' in part:
                    # Split the mixed format
                    date_part, price_part = part.split(' ', 1)
                    dates.append(date_part)
                    try:
                        all_numbers.append(float(price_part))
                    except ValueError:
                        pass
                elif '/' in part and len(part.split('/')) == 3:
                    # Pure date (YYYY/MM/DD format)
                    dates.append(part)
                elif ' ' in part:
                    # Handle mixed volume-price format like "1195 258.2756"
                    space_parts = part.split()
                    for space_part in space_parts:
                        try:
                            all_numbers.append(float(space_part))
                        except ValueError:
                            pass
                else:
                    # Single number
                    try:
                        all_numbers.append(float(part))
                    except ValueError:
                        pass
            
            logger.info(f"Extracted {len(dates)} dates and {len(all_numbers)} numbers for {stock_id}")
            
            if len(dates) == 0 or len(all_numbers) == 0:
                logger.warning("No valid dates or numbers found in broker response")
                return []
            
            # Step 2: Improved parsing - assume 5 values per date (OHLCV)
            values_per_date = 5
            expected_numbers = len(dates) * values_per_date
            
            if len(all_numbers) >= expected_numbers:
                # We have enough numbers - parse sequentially
                for i, date_str in enumerate(dates):
                    try:
                        trade_date = datetime.strptime(date_str, '%Y/%m/%d')
                        
                        # Calculate indices for this date's data
                        start_idx = i * values_per_date
                        
                        if start_idx + values_per_date <= len(all_numbers):
                            # Extract OHLCV values
                            open_price = all_numbers[start_idx]
                            high_price = all_numbers[start_idx + 1] 
                            low_price = all_numbers[start_idx + 2]
                            close_price = all_numbers[start_idx + 3]
                            volume = all_numbers[start_idx + 4]
                            
                            # Apply price scaling if needed (broker data often scaled by 100)
                            if open_price > 1000:
                                open_price = round(open_price / 100, 4)
                                high_price = round(high_price / 100, 4)
                                low_price = round(low_price / 100, 4)
                                close_price = round(close_price / 100, 4)
                            
                            # Basic validation - ensure prices are reasonable
                            if (all(p > 0 for p in [open_price, high_price, low_price, close_price]) and
                                low_price <= min(open_price, close_price) and
                                high_price >= max(open_price, close_price) and
                                high_price >= low_price and
                                volume >= 0):
                                
                                data_item = {
                                    "stock_code": stock_id,
                                    "trade_date": trade_date,
                                    "open_price": open_price,
                                    "high_price": high_price,
                                    "low_price": low_price,
                                    "close_price": close_price,
                                    "volume": int(volume)
                                }
                                
                                if self.validate_daily_data(data_item):
                                    daily_data.append(data_item)
                                    
                    except Exception as e:
                        logger.debug(f"Error parsing date {date_str}: {e}")
                        continue
                        
                logger.info(f"Sequential parsing extracted {len(daily_data)} valid records for {stock_id}")
            
            # Fallback: Use the original parsing methods if sequential parsing didn't work well
            if len(daily_data) < len(dates) * 0.5:  # If we got less than 50% of expected records
                logger.info(f"Sequential parsing yielded low results, trying alternative methods for {stock_id}")
                daily_data = []  # Reset
                
                # Method 1: Try different offset positions to find where actual price data starts
                for start_offset in [0, 1, 2, 3]:
                    if self._try_parse_with_offset(dates, all_numbers, start_offset, stock_id, daily_data):
                        logger.debug(f"Successfully parsed data with offset {start_offset}")
                        break
                
                # Method 2: If that fails, try to find realistic price ranges
                if not daily_data:
                    self._try_parse_by_price_range(dates, all_numbers, stock_id, daily_data)
        
        except Exception as e:
            logger.error(f"Error parsing broker response: {e}")
            return []
        
        logger.info(f"Final result: Parsed {len(daily_data)} records for stock {stock_id}")
        return daily_data
    
    def _try_parse_with_offset(self, dates, all_numbers, offset, stock_id, daily_data):
        """Try to parse data with a specific offset to find the correct alignment."""
        try:
            adjusted_numbers = all_numbers[offset:]
            if len(adjusted_numbers) < len(dates) * 4:
                return False
            
            data_per_date = len(adjusted_numbers) // len(dates)
            if data_per_date < 4:
                return False
            
            temp_data = []
            for i, date_str in enumerate(dates):
                try:
                    trade_date = datetime.strptime(date_str, '%Y/%m/%d')
                    
                    start_idx = i * data_per_date
                    end_idx = start_idx + min(5, data_per_date)
                    
                    if end_idx <= len(adjusted_numbers):
                        data_points = adjusted_numbers[start_idx:end_idx]
                        
                        if len(data_points) >= 4:
                            open_price = data_points[0]
                            high_price = data_points[1] 
                            low_price = data_points[2]
                            close_price = data_points[3]
                            volume = int(data_points[4]) if len(data_points) > 4 else 0
                            
                            # Apply price scaling if needed (convert from cents to dollars)
                            if all(p > 1000 for p in [open_price, high_price, low_price, close_price]):
                                open_price = round(open_price / 100, 2)
                                high_price = round(high_price / 100, 2)
                                low_price = round(low_price / 100, 2)
                                close_price = round(close_price / 100, 2)
                            
                            # Quick validation to see if this pattern makes sense
                            if (all(p > 0 for p in [open_price, high_price, low_price, close_price]) and
                                low_price <= min(open_price, close_price) and
                                high_price >= max(open_price, close_price) and
                                high_price >= low_price):
                                
                                data_item = {
                                    "stock_code": stock_id,  # Note: stock_id parameter is actually stock_code
                                    "trade_date": trade_date,
                                    "open_price": open_price,
                                    "high_price": high_price,
                                    "low_price": low_price,
                                    "close_price": close_price,
                                    "volume": volume
                                }
                                
                                if self.validate_daily_data(data_item):
                                    temp_data.append(data_item)
                
                except Exception:
                    continue
            
            # If we got at least 2 valid records, consider this successful
            if len(temp_data) >= 2:
                daily_data.extend(temp_data)
                return True
                
        except Exception:
            pass
        
        return False
    
    def _try_parse_by_price_range(self, dates, all_numbers, stock_id, daily_data):
        """Try to find realistic price data by looking for reasonable price ranges."""
        try:
            # Look for numbers in reasonable stock price range (10-2000 for Taiwan stocks)
            price_candidates = [num for num in all_numbers if 10 <= num <= 2000]
            volume_candidates = [num for num in all_numbers if num > 10000]
            
            if len(price_candidates) < len(dates) * 4:
                return
            
            # Try to group price candidates into OHLC sets
            for i, date_str in enumerate(dates[:3]):  # Try first 3 dates
                try:
                    trade_date = datetime.strptime(date_str, '%Y/%m/%d')
                    
                    # Take next 4 price candidates
                    start_idx = i * 4
                    if start_idx + 4 <= len(price_candidates):
                        prices = price_candidates[start_idx:start_idx + 4]
                        
                        # Sort to get potential OHLC
                        sorted_prices = sorted(prices)
                        
                        # Apply price scaling if needed
                        scaled_prices = []
                        for price in prices:
                            if price > 1000:
                                scaled_prices.append(round(price / 100, 2))
                            else:
                                scaled_prices.append(price)
                        
                        sorted_scaled_prices = sorted(scaled_prices)
                        
                        data_item = {
                            "stock_code": stock_id,  # Note: stock_id parameter is actually stock_code
                            "trade_date": trade_date,
                            "open_price": scaled_prices[0],      # Use original order
                            "high_price": sorted_scaled_prices[-1],  # Highest
                            "low_price": sorted_scaled_prices[0],    # Lowest  
                            "close_price": scaled_prices[-1],       # Use original order
                            "volume": volume_candidates[i] if i < len(volume_candidates) else 0
                        }
                        
                        if self.validate_daily_data(data_item):
                            daily_data.append(data_item)
                
                except Exception:
                    continue
                    
        except Exception:
            pass
    
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
            
            # 0. Smart skip: Check if data is up to date (unless force update)
            if not force_update and self.is_stock_data_up_to_date(stock_id):
                latest_date = self.get_latest_date_from_database(stock_id)
                result = {
                    "status": "skipped",
                    "stock_code": stock_id,
                    "records_processed": 0,
                    "created": 0,
                    "updated": 0,
                    "latest_date": latest_date.isoformat() if latest_date else None,
                    "reason": "Stock data is already up to date",
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"Skipped processing for {stock_id} - data already up to date")
                return result
            
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