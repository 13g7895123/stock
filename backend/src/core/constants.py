"""Application constants and enums.

集中管理所有常數，避免 magic numbers 和 magic strings。
"""
from enum import Enum
from typing import Final


# === Market Constants ===

class Market(str, Enum):
    """Stock market types."""
    TSE = "TSE"      # Taiwan Stock Exchange (上市)
    TPEX = "TPEx"    # Taipei Exchange (上櫃)
    EMERGING = "EMERGING"  # Emerging Stock Board (興櫃)


class DataSource(str, Enum):
    """Data source types."""
    TWSE = "TWSE"
    TPEX = "TPEx"
    BROKER = "broker_crawler"
    GO_CRAWLER = "go_crawler"
    MANUAL = "manual"


class DataQuality(str, Enum):
    """Data quality levels."""
    RAW = "raw"
    VALIDATED = "validated"
    CORRECTED = "corrected_daily"
    ADJUSTED = "adjusted"


# === Task Status ===

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types."""
    STOCK_SYNC = "stock_sync"
    DAILY_UPDATE = "daily_update"
    BATCH_UPDATE = "batch_update"
    MA_CALCULATION = "ma_calculation"
    INSTITUTIONAL = "institutional_trading"


# === Broker URLs ===

BROKER_URLS: Final[list[str]] = [
    "http://fubon-ebrokerdj.fbs.com.tw/",
    "http://justdata.moneydj.com/",
    "http://jdata.yuanta.com.tw/",
    "http://moneydj.emega.com.tw/",
    "http://djfubonholdingfund.fbs.com.tw/",
    "https://sjmain.esunsec.com.tw/",
    "http://kgieworld.moneydj.com/",
    "http://newjust.masterlink.com.tw/"
]


# === API URLs ===

class TwseUrls:
    """TWSE API URLs."""
    BASE = "https://www.twse.com.tw"
    STOCK_DAY_ALL = f"{BASE}/rwd/zh/afterTrading/STOCK_DAY_ALL"
    INSTITUTIONAL = f"{BASE}/rwd/zh/fund/T86"


class TpexUrls:
    """TPEx API URLs."""
    BASE = "https://www.tpex.org.tw"
    OPENAPI = f"{BASE}/openapi/v1/mopsfin_t187ap03_O"
    DAILY_QUOTES = f"{BASE}/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php"


# === Validation Constants ===

VALID_STOCK_SYMBOL_PATTERN: Final[str] = r"^[1-9]\d{3}$"
MIN_STOCK_SYMBOL: Final[int] = 1000
MAX_STOCK_SYMBOL: Final[int] = 9999

# Stock symbol must be 4 digits, not starting with 0
STOCK_SYMBOL_LENGTH: Final[int] = 4


# === Pagination Defaults ===

DEFAULT_PAGE_SIZE: Final[int] = 50
MAX_PAGE_SIZE: Final[int] = 1000
MIN_PAGE_SIZE: Final[int] = 1


# === Concurrency Defaults ===

DEFAULT_MAX_WORKERS: Final[int] = 4
MAX_WORKERS_LIMIT: Final[int] = 8
MIN_WORKERS: Final[int] = 1

DEFAULT_TIMEOUT_PER_STOCK: Final[float] = 120.0
MIN_TIMEOUT: Final[float] = 30.0
MAX_TIMEOUT: Final[float] = 300.0

DEFAULT_BATCH_SIZE: Final[int] = 10
MAX_BATCH_SIZE: Final[int] = 50
MIN_BATCH_SIZE: Final[int] = 1


# === HTTP Constants ===

DEFAULT_HTTP_TIMEOUT: Final[float] = 30.0
DEFAULT_RETRY_COUNT: Final[int] = 3
RETRY_DELAY_SECONDS: Final[float] = 1.0


# === Moving Average Periods ===

MA_PERIODS: Final[list[int]] = [5, 10, 20, 60, 120, 240]


# === Date Format ===

DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
ROC_DATE_FORMAT: Final[str] = "%Y/%m/%d"  # ROC year format
