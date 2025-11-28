"""Schemas package initialization.

Export all schemas for easy import.
"""
from src.schemas.common import (
    PaginationParams,
    PaginationInfo,
    SuccessResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    TaskStatusResponse,
    BatchOperationSummary,
    HealthCheckResponse,
    ComponentHealth,
)

from src.schemas.stock import (
    StockBaseSchema,
    StockListRequest,
    BatchUpdateRequest,
    ConcurrentBatchUpdateRequest,
    DateRangeRequest,
    StockResponse,
    StockListItemResponse,
    StockDailyDataResponse,
    StockSyncResultResponse,
    DailyDataUpdateResponse,
    BatchUpdateResultResponse,
    StockCountResponse,
    StockHistoryStatsResponse,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginationInfo",
    "SuccessResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "TaskStatusResponse",
    "BatchOperationSummary",
    "HealthCheckResponse",
    "ComponentHealth",
    # Stock
    "StockBaseSchema",
    "StockListRequest",
    "BatchUpdateRequest",
    "ConcurrentBatchUpdateRequest",
    "DateRangeRequest",
    "StockResponse",
    "StockListItemResponse",
    "StockDailyDataResponse",
    "StockSyncResultResponse",
    "DailyDataUpdateResponse",
    "BatchUpdateResultResponse",
    "StockCountResponse",
    "StockHistoryStatsResponse",
]
