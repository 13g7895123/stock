"""Date and time utilities.

集中管理日期時間相關的工具函數。
"""
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from src.core.constants import DATE_FORMAT, DATETIME_FORMAT, ROC_DATE_FORMAT


def get_today() -> date:
    """Get today's date."""
    return date.today()


def get_now() -> datetime:
    """Get current datetime."""
    return datetime.now()


def format_date(d: date, fmt: str = DATE_FORMAT) -> str:
    """Format date to string."""
    return d.strftime(fmt)


def format_datetime(dt: datetime, fmt: str = DATETIME_FORMAT) -> str:
    """Format datetime to string."""
    return dt.strftime(fmt)


def parse_date(date_str: str, fmt: str = DATE_FORMAT) -> date:
    """Parse date from string."""
    return datetime.strptime(date_str, fmt).date()


def parse_datetime(dt_str: str, fmt: str = DATETIME_FORMAT) -> datetime:
    """Parse datetime from string."""
    return datetime.strptime(dt_str, fmt)


def to_roc_date(d: date) -> str:
    """
    Convert date to ROC (Republic of China) format.
    ROC year = Western year - 1911
    
    Args:
        d: Date to convert
        
    Returns:
        Date string in ROC format (e.g., "113/01/15")
    """
    roc_year = d.year - 1911
    return f"{roc_year}/{d.month:02d}/{d.day:02d}"


def from_roc_date(roc_date_str: str) -> date:
    """
    Convert ROC date string to date object.
    
    Args:
        roc_date_str: ROC format date string (e.g., "113/01/15")
        
    Returns:
        Date object
    """
    parts = roc_date_str.split("/")
    roc_year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    western_year = roc_year + 1911
    return date(western_year, month, day)


def is_trading_day(d: date) -> bool:
    """
    Check if date is a potential trading day (weekday).
    Note: Does not check for holidays.
    
    Args:
        d: Date to check
        
    Returns:
        True if weekday, False if weekend
    """
    return d.weekday() < 5  # Monday = 0, Sunday = 6


def get_previous_trading_days(days: int = 7) -> Tuple[date, ...]:
    """
    Get list of previous potential trading days.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Tuple of dates (most recent first)
    """
    result = []
    current = get_today()
    
    while len(result) < days:
        if is_trading_day(current):
            result.append(current)
        current -= timedelta(days=1)
    
    return tuple(result)


def days_between(d1: date, d2: date) -> int:
    """
    Calculate days between two dates.
    
    Args:
        d1: First date
        d2: Second date
        
    Returns:
        Number of days (absolute value)
    """
    return abs((d2 - d1).days)


def is_data_stale(last_update: Optional[datetime], max_age_days: int = 7) -> bool:
    """
    Check if data is stale based on last update time.
    
    Args:
        last_update: Last update datetime
        max_age_days: Maximum age in days before data is considered stale
        
    Returns:
        True if data is stale or last_update is None
    """
    if last_update is None:
        return True
    
    if isinstance(last_update, datetime):
        last_update_date = last_update.date()
    else:
        last_update_date = last_update
    
    return days_between(last_update_date, get_today()) > max_age_days
