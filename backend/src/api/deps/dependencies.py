"""API dependencies for dependency injection.

集中管理所有 API 的依賴項，實現更好的解耦和可測試性。
"""
from typing import Generator, Optional

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.common import PaginationParams
from src.services.stock_list_service import StockListService
from src.services.daily_data_service import DailyDataService


# === Database Dependencies ===

def get_database() -> Generator[Session, None, None]:
    """Get database session dependency."""
    yield from get_db()


# === Pagination Dependencies ===

def get_pagination(
    page: int = Query(1, ge=1, description="頁數"),
    limit: int = Query(50, ge=1, le=1000, description="每頁筆數")
) -> PaginationParams:
    """Get pagination parameters dependency."""
    return PaginationParams(page=page, limit=limit)


# === Service Dependencies ===

def get_stock_list_service(
    db: Session = Depends(get_database)
) -> StockListService:
    """Get StockListService instance."""
    return StockListService(db_session=db)


def get_daily_data_service(
    db: Session = Depends(get_database)
) -> DailyDataService:
    """Get DailyDataService instance."""
    return DailyDataService(db_session=db)


# === Query Parameter Dependencies ===

class StockQueryParams:
    """Stock query parameters."""
    
    def __init__(
        self,
        market: Optional[str] = Query(None, description="市場篩選 (TSE/TPEx)"),
        search: Optional[str] = Query(None, max_length=100, description="搜尋股票代號或名稱"),
        is_active: bool = Query(True, description="只顯示啟用的股票")
    ):
        self.market = market
        self.search = search
        self.is_active = is_active


def get_stock_query_params(
    market: Optional[str] = Query(None, description="市場篩選 (TSE/TPEx)"),
    search: Optional[str] = Query(None, max_length=100, description="搜尋股票代號或名稱"),
    is_active: bool = Query(True, description="只顯示啟用的股票")
) -> StockQueryParams:
    """Get stock query parameters dependency."""
    return StockQueryParams(market=market, search=search, is_active=is_active)
