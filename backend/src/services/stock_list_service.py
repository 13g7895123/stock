"""Stock list service - 股票列表擷取服務."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.stock import Stock
from src.core.config import settings

logger = logging.getLogger(__name__)


class StockListService:
    """Service for fetching and managing stock lists from external APIs."""
    
    # 台灣證券交易所 API URLs
    TSE_STOCK_LIST_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL"
    TPEX_STOCK_LIST_URL = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php"
    
    def __init__(self, db_session: Session = None):
        """Initialize the stock list service."""
        self.db_session = db_session
        self.timeout = httpx.Timeout(30.0)
        
    def filter_valid_stocks(self, raw_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter stocks to only include valid 4-digit non-zero-prefix symbols."""
        valid_stocks = []
        
        for stock in raw_stocks:
            symbol = stock.get("symbol", "").strip()
            
            # 檢查是否為4位數且不以0開頭
            if (len(symbol) == 4 and 
                symbol.isdigit() and 
                not symbol.startswith("0")):
                valid_stocks.append(stock)
                logger.debug(f"Valid stock: {symbol}")
            else:
                logger.debug(f"Filtered out stock: {symbol} (invalid format)")
        
        logger.info(f"Filtered {len(valid_stocks)} valid stocks from {len(raw_stocks)} raw stocks")
        return valid_stocks
    
    async def fetch_tse_stocks(self) -> List[Dict[str, Any]]:
        """Fetch stock list from TSE (Taiwan Stock Exchange)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 使用上市股票清單API
                response = await client.get(
                    "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL",
                    params={
                        "date": "20241209",  # 使用當前日期格式
                        "response": "json"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("stat") != "OK":
                    raise Exception(f"TSE API returned error: {data.get('stat')}")
                
                stocks = []
                for item in data.get("data", []):
                    if len(item) >= 2:  # 確保有足夠的欄位
                        symbol = item[0].strip()
                        name = item[1].strip()
                        
                        stocks.append({
                            "symbol": symbol,
                            "name": name,
                            "market": "TSE"
                        })
                
                logger.info(f"Fetched {len(stocks)} stocks from TSE")
                return stocks
                
        except httpx.TimeoutException:
            logger.error("Timeout while fetching TSE stocks")
            raise Exception("TSE API timeout")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while fetching TSE stocks: {e}")
            raise Exception(f"TSE API HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error fetching TSE stocks: {e}")
            raise
    
    async def fetch_tpex_stocks(self) -> List[Dict[str, Any]]:
        """Fetch stock list from TPEx (Taipei Exchange)."""
        logger.info("Fetching TPEx stocks...")
        
        # Use official TPEx OpenAPI endpoint
        api_url = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Trying official TPEx OpenAPI: {api_url}")
                
                response = await client.get(api_url)
                response.raise_for_status()
                
                data = response.json()
                stocks = self._parse_tpex_openapi_response(data)
                
                if stocks:
                    logger.info(f"Successfully fetched {len(stocks)} stocks from TPEx OpenAPI")
                    return stocks
                else:
                    logger.warning("No stocks returned from TPEx OpenAPI")
                    raise Exception("No stocks found in TPEx OpenAPI response")
                        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with TPEx OpenAPI: {e}")
            raise Exception(f"TPEx OpenAPI HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error with TPEx OpenAPI: {e}")
            raise Exception(f"TPEx OpenAPI error: {e}")

    def _get_current_tpex_date_params(self) -> Dict[str, str]:
        """Get current date parameters for TPEx API in ROC format."""
        from datetime import datetime, timedelta
        
        # Try current date first, then previous business day
        dates_to_try = []
        today = datetime.now()
        
        # Add today and last 7 days (to handle weekends/holidays)
        for i in range(8):
            date = today - timedelta(days=i)
            roc_year = date.year - 1911  # Convert to ROC year
            roc_date = f"{roc_year}/{date.month:02d}/{date.day:02d}"
            dates_to_try.append(roc_date)
        
        # Return the most recent date (today)
        return {
            "date": dates_to_try[0],
            "response": "json"
        }

    def _parse_tpex_listing_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse TPEx listing API response."""
        stocks = []
        
        if data.get("stat") == "OK" and "aaData" in data:
            for item in data["aaData"]:
                if len(item) >= 2:
                    symbol = item[0].strip() if item[0] else ""
                    name = item[1].strip() if item[1] else ""
                    
                    if symbol and name:
                        stocks.append({
                            "symbol": symbol,
                            "name": name,
                            "market": "TPEx"
                        })
        
        return stocks

    def _parse_tpex_daily_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse TPEx daily quotes API response."""
        stocks = []
        
        if data.get("stat") == "OK" and "aaData" in data:
            for item in data["aaData"]:
                if len(item) >= 2:
                    symbol = item[0].strip() if item[0] else ""
                    name = item[1].strip() if item[1] else ""
                    
                    if symbol and name:
                        stocks.append({
                            "symbol": symbol,
                            "name": name,
                            "market": "TPEx"
                        })
        
        return stocks
    
    def _parse_tpex_openapi_response(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse TPEx OpenAPI response for stock list."""
        stocks = []
        
        if isinstance(data, list):
            for item in data:
                # Extract stock symbol and company name
                symbol = item.get("SecuritiesCompanyCode", "").strip()
                name = item.get("CompanyName", "").strip()
                
                if symbol and name:
                    stocks.append({
                        "symbol": symbol,
                        "name": name,
                        "market": "TPEx"
                    })
                    logger.debug(f"Added TPEx stock: {symbol} - {name}")
        
        logger.info(f"Parsed {len(stocks)} stocks from TPEx OpenAPI")
        return stocks
    
    async def fetch_all_stocks(self) -> tuple[List[Dict[str, Any]], List[str]]:
        """Fetch all stocks from both TSE and TPEx. Returns (stocks, errors)."""
        all_stocks = []
        errors = []
        tse_stocks = []
        tpex_stocks = []
        
        # 嘗試擷取TSE股票
        try:
            tse_stocks = await self.fetch_tse_stocks()
            all_stocks.extend(tse_stocks)
            logger.info(f"TSE stocks fetched successfully: {len(tse_stocks)} stocks")
        except Exception as e:
            error_msg = f"TSE API error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # 嘗試擷取TPEx股票
        try:
            tpex_stocks = await self.fetch_tpex_stocks()
            all_stocks.extend(tpex_stocks)
            logger.info(f"TPEx stocks fetched successfully: {len(tpex_stocks)} stocks")
        except Exception as e:
            error_msg = f"TPEx API error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # 如果兩個API都失敗，拋出異常
        if not all_stocks:
            raise Exception(f"All stock APIs failed: {'; '.join(errors)}")
        
        logger.info(f"Fetched total {len(all_stocks)} stocks (TSE: {len(tse_stocks)}, TPEx: {len(tpex_stocks)})")
        
        # 過濾出有效股票（4位數非0開頭）
        valid_stocks = self.filter_valid_stocks(all_stocks)
        
        return valid_stocks, errors
    
    def validate_stock_data(self, stock_data: Dict[str, Any]) -> bool:
        """Validate stock data format and required fields."""
        required_fields = ["symbol", "name", "market"]
        
        for field in required_fields:
            if field not in stock_data or not stock_data[field]:
                logger.warning(f"Missing required field: {field} in stock data: {stock_data}")
                return False
        
        symbol = stock_data["symbol"]
        if not re.match(r"^[1-9]\d{3}$", symbol):
            logger.warning(f"Invalid stock symbol format: {symbol}")
            return False
            
        market = stock_data["market"]
        if market not in ["TSE", "TPEx"]:
            logger.warning(f"Invalid market: {market}")
            return False
            
        return True
    
    def save_stocks_to_database(self, stocks: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Save stocks to database. Returns (created, updated) counts."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        created_count = 0
        updated_count = 0
        
        for stock_data in stocks:
            if not self.validate_stock_data(stock_data):
                continue
                
            symbol = stock_data["symbol"]
            existing_stock = self.db_session.query(Stock).filter(
                Stock.stock_code == symbol
            ).first()
            
            if existing_stock:
                # 更新既有股票
                existing_stock.stock_name = stock_data["name"]
                existing_stock.market = stock_data["market"]
                existing_stock.is_active = True
                updated_count += 1
                logger.debug(f"Updated stock: {symbol}")
            else:
                # 新增股票
                new_stock = Stock(
                    stock_code=symbol,
                    stock_name=stock_data["name"],
                    market=stock_data["market"],
                    is_active=True
                )
                self.db_session.add(new_stock)
                created_count += 1
                logger.debug(f"Created new stock: {symbol}")
        
        self.db_session.commit()
        logger.info(f"Database operation completed: {created_count} created, {updated_count} updated")
        
        return created_count, updated_count
    
    def get_stocks_from_database(self, active_only: bool = True) -> List[Stock]:
        """Get all stocks from database."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        query = self.db_session.query(Stock)
        if active_only:
            query = query.filter(Stock.is_active == True)
            
        stocks = query.all()
        logger.info(f"Retrieved {len(stocks)} stocks from database (active_only={active_only})")
        
        return stocks
    
    def deactivate_missing_stocks(self, current_symbols: List[str]) -> int:
        """Deactivate stocks that are no longer in the fetched data."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        # 找出資料庫中有但當前擷取清單沒有的股票
        missing_stocks = self.db_session.query(Stock).filter(
            Stock.is_active == True,
            ~Stock.stock_code.in_(current_symbols)
        ).all()
        
        deactivated_count = 0
        for stock in missing_stocks:
            stock.is_active = False
            deactivated_count += 1
            logger.debug(f"Deactivated stock: {stock.stock_code}")
        
        if deactivated_count > 0:
            self.db_session.commit()
            logger.info(f"Deactivated {deactivated_count} missing stocks")
        
        return deactivated_count
    
    def get_stock_count_by_market(self) -> Dict[str, int]:
        """Get stock counts grouped by market."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        counts = self.db_session.query(
            Stock.market,
            func.count(Stock.id)
        ).filter(
            Stock.is_active == True
        ).group_by(Stock.market).all()
        
        result = {market: count for market, count in counts}
        logger.info(f"Stock counts by market: {result}")
        
        return result
    
    async def sync_all_stocks(self) -> Dict[str, Any]:
        """Perform complete stock synchronization."""
        if not self.db_session:
            raise Exception("Database session not provided")
        
        try:
            logger.info("Starting complete stock synchronization")
            
            # 1. 擷取所有股票 (取得股票和錯誤)
            stocks, errors = await self.fetch_all_stocks()
            
            # 2. 儲存到資料庫
            created_count, updated_count = self.save_stocks_to_database(stocks)
            
            # 3. 停用遺失的股票
            current_symbols = [stock["symbol"] for stock in stocks]
            deactivated_count = self.deactivate_missing_stocks(current_symbols)
            
            # 4. 取得統計資訊
            market_counts = self.get_stock_count_by_market()
            
            # 5. 計算各市場股票數量
            tse_stocks = [s for s in stocks if s.get("market") == "TSE"]
            tpex_stocks = [s for s in stocks if s.get("market") == "TPEx"]
            
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            
            # 決定狀態
            if errors:
                status = "partial_success" if stocks else "error"
                message = "Some APIs failed but data was still retrieved" if stocks else "All APIs failed"
            else:
                status = "success"
                message = "Stock synchronization completed successfully"
            
            result = {
                "status": status,
                "message": message,
                "total_stocks": len(stocks),
                "tse_stocks": len(tse_stocks),
                "tpex_stocks": len(tpex_stocks),
                "filtered_stocks": len(stocks),
                "new_stocks": created_count,
                "updated_stocks": updated_count,
                "deactivated_stocks": deactivated_count,
                "timestamp": timestamp,
                "market_counts": market_counts
            }
            
            # 包含錯誤資訊（如果有的話）
            if errors:
                result["errors"] = errors
            
            logger.info(f"Stock synchronization completed: {result['status']} - {result['total_stocks']} stocks")
            return result
            
        except Exception as e:
            logger.error(f"Error during stock synchronization: {e}")
            from datetime import datetime
            result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return result