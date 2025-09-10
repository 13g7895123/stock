"""股票歷史資料更新服務

提供從外部API擷取股票歷史資料並更新到資料庫的功能。
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.stock import StockDailyData
from src.core.config import settings

logger = logging.getLogger(__name__)


class StockDataUpdater:
    """股票歷史資料更新服務"""
    
    def __init__(self, db_session: Session):
        """初始化服務
        
        Args:
            db_session: 資料庫會話
        """
        self.db_session = db_session
        self.timeout = httpx.Timeout(30.0)
    
    def get_latest_data_date(self, symbol: str) -> Optional[date]:
        """取得股票在資料庫中的最新資料日期
        
        Args:
            symbol: 股票代號
            
        Returns:
            Optional[date]: 最新資料日期，如無資料則回傳None
        """
        try:
            latest_record = (
                self.db_session.query(StockDailyData)
                .filter(StockDailyData.stock_id == symbol)
                .order_by(StockDailyData.trade_date.desc())
                .first()
            )
            
            if latest_record and hasattr(latest_record.trade_date, 'date'):
                return latest_record.trade_date.date()
            elif latest_record:
                return latest_record.trade_date
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest data date for {symbol}: {e}")
            return None
    
    async def fetch_historical_data_from_twse(
        self, 
        symbol: str, 
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """從台灣證券交易所API擷取歷史資料
        
        Args:
            symbol: 股票代號
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            List[Dict[str, Any]]: 歷史資料列表
        """
        data = []
        current_date = start_date
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while current_date <= end_date:
                    # 每次請求一個月的資料
                    year = current_date.year
                    month = current_date.month
                    
                    logger.info(f"Fetching TWSE data for {symbol} - {year}/{month:02d}")
                    
                    # 台灣證券交易所API
                    url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
                    params = {
                        "response": "json",
                        "date": f"{year}{month:02d}01",
                        "stockNo": symbol
                    }
                    
                    try:
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        
                        json_data = response.json()
                        
                        if json_data.get("stat") == "OK" and "data" in json_data:
                            # 解析資料
                            for row in json_data["data"]:
                                if len(row) >= 9:
                                    try:
                                        # 解析日期 (民國年/月/日)
                                        date_parts = row[0].split('/')
                                        if len(date_parts) == 3:
                                            roc_year = int(date_parts[0])
                                            month_num = int(date_parts[1])
                                            day_num = int(date_parts[2])
                                            trade_date = date(roc_year + 1911, month_num, day_num)
                                            
                                            # 確保在指定日期範圍內
                                            if start_date <= trade_date <= end_date:
                                                data.append({
                                                    "symbol": symbol,
                                                    "trade_date": trade_date,
                                                    "volume": int(row[1].replace(',', '')),
                                                    "amount": float(row[2].replace(',', '')),
                                                    "open_price": float(row[3].replace(',', '')),
                                                    "high_price": float(row[4].replace(',', '')),
                                                    "low_price": float(row[5].replace(',', '')),
                                                    "close_price": float(row[6].replace(',', '')),
                                                    "change": float(row[7].replace(',', '')) if row[7] != '--' else 0.0,
                                                    "transaction": int(row[8].replace(',', ''))
                                                })
                                    except (ValueError, IndexError) as e:
                                        logger.warning(f"Error parsing row for {symbol}: {e}")
                                        continue
                        else:
                            logger.warning(f"No data returned for {symbol} - {year}/{month:02d}: {json_data.get('stat')}")
                    
                    except httpx.HTTPError as e:
                        logger.error(f"HTTP error fetching TWSE data for {symbol} - {year}/{month:02d}: {e}")
                    except Exception as e:
                        logger.error(f"Error fetching TWSE data for {symbol} - {year}/{month:02d}: {e}")
                    
                    # 移到下個月
                    if month == 12:
                        current_date = date(year + 1, 1, 1)
                    else:
                        current_date = date(year, month + 1, 1)
                    
                    # 避免請求過於頻繁
                    await asyncio.sleep(1)
            
            logger.info(f"Fetched {len(data)} records for {symbol} from TWSE")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data from TWSE for {symbol}: {e}")
            return []
    
    def save_stock_data(self, symbol: str, data: List[Dict[str, Any]]) -> int:
        """儲存股票資料到資料庫
        
        Args:
            symbol: 股票代號
            data: 股票資料列表
            
        Returns:
            int: 成功儲存的筆數
        """
        if not data:
            return 0
        
        saved_count = 0
        
        try:
            for record in data:
                # 檢查是否已存在
                existing = self.db_session.query(StockDailyData).filter(
                    StockDailyData.stock_id == symbol,
                    StockDailyData.trade_date == record["trade_date"]
                ).first()
                
                if not existing:
                    # 計算還原收盤價 (簡化處理，這裡暫時等同於收盤價)
                    adjusted_close = record.get("close_price", 0.0)
                    
                    new_record = StockDailyData(
                        stock_id=symbol,
                        trade_date=record["trade_date"],
                        open_price=record.get("open_price", 0.0),
                        high_price=record.get("high_price", 0.0),
                        low_price=record.get("low_price", 0.0),
                        close_price=record.get("close_price", 0.0),
                        volume=record.get("volume", 0),
                        adjusted_close=adjusted_close
                    )
                    
                    self.db_session.add(new_record)
                    saved_count += 1
                else:
                    logger.debug(f"Data already exists for {symbol} on {record['trade_date']}")
            
            self.db_session.commit()
            logger.info(f"Saved {saved_count} new records for {symbol}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {e}")
            self.db_session.rollback()
            return 0
    
    async def update_stock_data(
        self, 
        symbol: str, 
        days_back: int = 365,
        force_full_update: bool = False
    ) -> Dict[str, Any]:
        """更新單一股票的歷史資料
        
        Args:
            symbol: 股票代號
            days_back: 回溯天數 (預設365天)
            force_full_update: 是否強制完整更新
            
        Returns:
            Dict[str, Any]: 更新結果
        """
        logger.info(f"Starting data update for stock {symbol}")
        
        try:
            # 決定更新的日期範圍
            end_date = date.today()
            
            if force_full_update:
                # 強制完整更新
                start_date = end_date - timedelta(days=days_back)
            else:
                # 增量更新：從最後一筆資料的日期開始
                latest_date = self.get_latest_data_date(symbol)
                if latest_date:
                    start_date = latest_date + timedelta(days=1)  # 從下一天開始
                    if start_date > end_date:
                        return {
                            "status": "success",
                            "symbol": symbol,
                            "message": "Data is already up to date",
                            "records_updated": 0,
                            "latest_date": latest_date.isoformat()
                        }
                else:
                    # 沒有歷史資料，進行完整更新
                    start_date = end_date - timedelta(days=days_back)
            
            logger.info(f"Updating {symbol} data from {start_date} to {end_date}")
            
            # 擷取資料
            data = await self.fetch_historical_data_from_twse(symbol, start_date, end_date)
            
            # 儲存資料
            records_saved = self.save_stock_data(symbol, data)
            
            return {
                "status": "success",
                "symbol": symbol,
                "records_updated": records_saved,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating data for {symbol}: {e}")
            return {
                "status": "error",
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def update_multiple_stocks(
        self, 
        symbols: List[str], 
        days_back: int = 365,
        force_full_update: bool = False
    ) -> Dict[str, Any]:
        """批量更新多支股票的歷史資料
        
        Args:
            symbols: 股票代號列表
            days_back: 回溯天數
            force_full_update: 是否強制完整更新
            
        Returns:
            Dict[str, Any]: 批量更新結果
        """
        logger.info(f"Starting bulk data update for {len(symbols)} stocks")
        
        start_time = datetime.utcnow()
        results = {}
        success_count = 0
        error_count = 0
        total_records = 0
        
        try:
            for i, symbol in enumerate(symbols):
                logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
                
                result = await self.update_stock_data(symbol, days_back, force_full_update)
                results[symbol] = result
                
                if result["status"] == "success":
                    success_count += 1
                    total_records += result["records_updated"]
                else:
                    error_count += 1
                
                # 避免請求過於頻繁
                await asyncio.sleep(0.5)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "completed",
                "total_symbols": len(symbols),
                "success_count": success_count,
                "error_count": error_count,
                "total_records_updated": total_records,
                "execution_time_seconds": execution_time,
                "results": results,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in bulk data update: {e}")
            return {
                "status": "error",
                "error": str(e),
                "partial_results": results,
                "timestamp": datetime.utcnow().isoformat()
            }