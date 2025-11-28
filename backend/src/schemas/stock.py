"""Stock related Pydantic schemas.

定義股票相關的請求和回應模型。
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.constants import Market, DataSource, DataQuality


# === Base Schemas ===

class StockBaseSchema(BaseModel):
    """Base schema for stock data."""
    stock_code: str = Field(..., min_length=4, max_length=4, description="股票代號")
    stock_name: str = Field(..., min_length=1, max_length=255, description="股票名稱")
    market: str = Field(..., description="市場別 (TSE/TPEx)")

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, v: str) -> str:
        """Validate stock code format."""
        if not v.isdigit() or v.startswith("0") or len(v) != 4:
            raise ValueError("Stock code must be a 4-digit number not starting with 0")
        return v

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        """Validate market type."""
        valid_markets = [m.value for m in Market]
        if v not in valid_markets:
            raise ValueError(f"Market must be one of: {valid_markets}")
        return v


# === Request Schemas ===

class StockListRequest(BaseModel):
    """Request schema for stock list query."""
    page: int = Field(default=1, ge=1, description="頁數")
    limit: int = Field(default=50, ge=1, le=1000, description="每頁筆數")
    market: Optional[str] = Field(default=None, description="市場篩選 (TSE/TPEx)")
    search: Optional[str] = Field(default=None, max_length=100, description="搜尋股票代號或名稱")
    is_active: bool = Field(default=True, description="只顯示啟用的股票")


class BatchUpdateRequest(BaseModel):
    """Request schema for batch update operations."""
    symbols: Optional[List[str]] = Field(default=None, description="股票代號列表，若為空則更新所有股票")
    force_update: bool = Field(default=False, description="強制更新（忽略快取）")

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean symbol list."""
        if v is None:
            return None
        validated = []
        for symbol in v:
            symbol = symbol.strip().upper()
            if len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
                validated.append(symbol)
        return validated if validated else None


class ConcurrentBatchUpdateRequest(BatchUpdateRequest):
    """Request schema for concurrent batch update."""
    max_workers: int = Field(default=4, ge=1, le=8, description="最大併發執行緒數")
    timeout_per_stock: float = Field(default=120.0, ge=30, le=300, description="每檔股票超時時間(秒)")
    batch_size: int = Field(default=10, ge=1, le=50, description="批次大小")


class DateRangeRequest(BaseModel):
    """Request schema for date range queries."""
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate end_date is after start_date."""
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


# === Response Schemas ===

class StockResponse(StockBaseSchema):
    """Response schema for single stock."""
    id: int
    industry: Optional[str] = None
    capital_stock: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockListItemResponse(BaseModel):
    """Response schema for stock list item."""
    code: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    market: str = Field(..., description="市場別")
    industry: str = Field(default="未分類", description="產業別")
    price: float = Field(default=0.0, description="目前價格")
    change: float = Field(default=0.0, description="漲跌幅")
    data_status: str = Field(default="complete", description="資料狀態")
    last_update: str = Field(default="即時", description="最後更新時間")


class StockDailyDataResponse(BaseModel):
    """Response schema for daily stock data."""
    stock_code: str
    trade_date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    data_source: str
    data_quality: Optional[str] = None

    class Config:
        from_attributes = True


class StockSyncResultResponse(BaseModel):
    """Response schema for stock sync operation."""
    status: str
    message: str
    total_stocks: int
    tse_stocks: int
    tpex_stocks: int
    new_stocks: int
    updated_stocks: int
    deactivated_stocks: int
    timestamp: str
    market_counts: Dict[str, int]
    errors: Optional[List[str]] = None


class DailyDataUpdateResponse(BaseModel):
    """Response schema for daily data update."""
    status: str
    stock_symbol: str
    message: str
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    timestamp: str
    data_sources: str = "8 broker websites"
    data_quality: str = "adjusted_daily_prices"


class BatchUpdateResultResponse(BaseModel):
    """Response schema for batch update result."""
    status: str
    message: str
    data_source: str
    summary: Dict[str, Any]
    results: Dict[str, Any]
    timestamp: str


# === Statistics Schemas ===

class StockCountResponse(BaseModel):
    """Response schema for stock count."""
    total: int = Field(..., description="總股票數")
    tse: int = Field(default=0, description="上市股票數")
    tpex: int = Field(default=0, description="上櫃股票數")
    active: int = Field(default=0, description="活躍股票數")


class StockHistoryStatsResponse(BaseModel):
    """Response schema for stock history statistics."""
    stock_code: str
    total_records: int
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None
    has_data: bool = False
    days_of_data: int = 0
