"""股票歷史資料查詢服務

提供股票歷史資料查詢功能，包含：
- 基本資料查詢
- 日期範圍篩選
- 分頁功能  
- 排序功能
- 資料驗證
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from src.models.stock import StockDailyData

logger = logging.getLogger(__name__)


class StockHistoryService:
    """股票歷史資料查詢服務類別"""
    
    def __init__(self, db_session: Session):
        """初始化服務
        
        Args:
            db_session: 資料庫會話
        """
        self.db_session = db_session
    
    def validate_stock_symbol(self, symbol: str) -> bool:
        """驗證股票代號格式
        
        Args:
            symbol: 股票代號
            
        Returns:
            bool: 是否為有效格式
        """
        if not symbol or len(symbol) != 4:
            return False
        
        if not symbol.isdigit():
            return False
            
        if symbol.startswith("0"):
            return False
            
        return True
    
    def validate_date_range(self, start_date: Optional[str], end_date: Optional[str]) -> tuple:
        """驗證日期範圍
        
        Args:
            start_date: 開始日期字串 (YYYY-MM-DD)
            end_date: 結束日期字串 (YYYY-MM-DD)
            
        Returns:
            tuple: (parsed_start_date, parsed_end_date)
            
        Raises:
            ValueError: 日期格式錯誤時
        """
        parsed_start = None
        parsed_end = None
        
        if start_date:
            try:
                parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
        
        if end_date:
            try:
                parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")
        
        # 檢查日期邏輯
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise ValueError("start_date cannot be later than end_date")
            
        return parsed_start, parsed_end
    
    def validate_pagination(self, page: int, limit: int) -> None:
        """驗證分頁參數
        
        Args:
            page: 頁數
            limit: 每頁數量
            
        Raises:
            ValueError: 參數無效時
        """
        if page < 1:
            raise ValueError("page must be >= 1")
            
        if limit < 1:
            raise ValueError("limit must be >= 1")
            
        if limit > 1000:
            raise ValueError("limit cannot exceed 1000")
    
    def get_stock_history(
        self, 
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "trade_date",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """查詢股票歷史資料
        
        Args:
            symbol: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            page: 頁數 (從1開始)
            limit: 每頁數量
            sort_by: 排序欄位 (trade_date, close_price, volume)
            sort_order: 排序方向 (asc, desc)
            
        Returns:
            Dict[str, Any]: 查詢結果
            
        Raises:
            ValueError: 參數驗證失敗時
        """
        try:
            # 參數驗證
            if not self.validate_stock_symbol(symbol):
                raise ValueError(f"Invalid stock symbol: {symbol}. Must be 4-digit number not starting with 0.")
            
            parsed_start, parsed_end = self.validate_date_range(start_date, end_date)
            self.validate_pagination(page, limit)
            
            # 建立查詢
            query = self.db_session.query(StockDailyData).filter(
                StockDailyData.stock_id == symbol
            )
            
            # 日期範圍篩選
            if parsed_start:
                query = query.filter(StockDailyData.trade_date >= parsed_start)
            
            if parsed_end:
                query = query.filter(StockDailyData.trade_date <= parsed_end)
            
            # 取得總數量
            total_records = query.count()
            
            # 排序
            sort_column = getattr(StockDailyData, sort_by, StockDailyData.trade_date)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # 分頁
            offset = (page - 1) * limit
            results = query.offset(offset).limit(limit).all()
            
            # 轉換資料格式
            data = []
            for record in results:
                data.append({
                    "trade_date": record.trade_date.strftime('%Y-%m-%d') if isinstance(record.trade_date, (date, datetime)) else str(record.trade_date),
                    "open_price": float(record.open_price),
                    "high_price": float(record.high_price),
                    "low_price": float(record.low_price),
                    "close_price": float(record.close_price),
                    "volume": int(record.volume),
                    "adjusted_close": float(record.adjusted_close)
                })
            
            # 計算分頁資訊
            total_pages = (total_records + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1
            
            logger.info(f"Successfully retrieved {len(data)} records for stock {symbol}")
            
            return {
                "status": "success",
                "stock_symbol": symbol,
                "data": data,
                "total_records": total_records,
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                },
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_previous
                },
                "message": f"Retrieved {len(data)} records for stock {symbol}"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving stock history for {symbol}: {e}")
            raise
    
    def get_latest_trade_date(self, symbol: str) -> Optional[datetime]:
        """取得股票最新交易日期
        
        Args:
            symbol: 股票代號
            
        Returns:
            Optional[datetime]: 最新交易日期，如無資料則回傳None
        """
        try:
            if not self.validate_stock_symbol(symbol):
                raise ValueError(f"Invalid stock symbol: {symbol}")
            
            latest_record = (
                self.db_session.query(StockDailyData)
                .filter(StockDailyData.stock_id == symbol)
                .order_by(desc(StockDailyData.trade_date))
                .first()
            )
            
            return latest_record.trade_date if latest_record else None
            
        except Exception as e:
            logger.error(f"Error getting latest trade date for {symbol}: {e}")
            return None
    
    def get_stock_statistics(self, symbol: str) -> Dict[str, Any]:
        """取得股票統計資訊
        
        Args:
            symbol: 股票代號
            
        Returns:
            Dict[str, Any]: 統計資訊
        """
        try:
            if not self.validate_stock_symbol(symbol):
                raise ValueError(f"Invalid stock symbol: {symbol}")
            
            query = self.db_session.query(StockDailyData).filter(
                StockDailyData.stock_id == symbol
            )
            
            total_records = query.count()
            
            if total_records == 0:
                return {
                    "stock_symbol": symbol,
                    "total_records": 0,
                    "date_range": None,
                    "price_range": None
                }
            
            # 取得日期範圍
            earliest_record = query.order_by(asc(StockDailyData.trade_date)).first()
            latest_record = query.order_by(desc(StockDailyData.trade_date)).first()
            
            # 計算價格範圍（最近30天）
            recent_query = query.order_by(desc(StockDailyData.trade_date)).limit(30)
            recent_records = recent_query.all()
            
            prices = []
            for record in recent_records:
                prices.extend([record.high_price, record.low_price])
            
            return {
                "stock_symbol": symbol,
                "total_records": total_records,
                "date_range": {
                    "earliest": earliest_record.trade_date.strftime('%Y-%m-%d'),
                    "latest": latest_record.trade_date.strftime('%Y-%m-%d')
                },
                "price_range": {
                    "min_recent": min(prices) if prices else None,
                    "max_recent": max(prices) if prices else None,
                    "recent_days": len(recent_records)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics for {symbol}: {e}")
            raise