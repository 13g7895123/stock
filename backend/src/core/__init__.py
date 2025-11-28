"""Core package initialization.

Export commonly used core modules.
"""
from src.core.config import settings, get_settings
from src.core.database import get_db, create_tables, Base
from src.core.exceptions import (
    BaseAppException,
    DatabaseException,
    RecordNotFoundException,
    DuplicateRecordException,
    ValidationException,
    InvalidStockSymbolException,
    ExternalServiceException,
    BrokerServiceException,
    TWseApiException,
    TpexApiException,
    BusinessLogicException,
    DataNotAvailableException,
    RateLimitException,
)
from src.core.constants import (
    Market,
    DataSource,
    DataQuality,
    TaskStatus,
    TaskType,
    BROKER_URLS,
    MA_PERIODS,
)
from src.core.response import (
    success_response,
    paginated_response,
    error_response,
    PaginationInfo,
    ApiResponse,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Database
    "get_db",
    "create_tables",
    "Base",
    # Exceptions
    "BaseAppException",
    "DatabaseException",
    "RecordNotFoundException",
    "DuplicateRecordException",
    "ValidationException",
    "InvalidStockSymbolException",
    "ExternalServiceException",
    "BrokerServiceException",
    "TWseApiException",
    "TpexApiException",
    "BusinessLogicException",
    "DataNotAvailableException",
    "RateLimitException",
    # Constants
    "Market",
    "DataSource",
    "DataQuality",
    "TaskStatus",
    "TaskType",
    "BROKER_URLS",
    "MA_PERIODS",
    # Response
    "success_response",
    "paginated_response",
    "error_response",
    "PaginationInfo",
    "ApiResponse",
]