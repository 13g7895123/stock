"""Stock validation utilities.

集中管理股票相關的驗證邏輯。
"""
import re
from typing import List, Optional

from src.core.constants import VALID_STOCK_SYMBOL_PATTERN, Market
from src.core.exceptions import InvalidStockSymbolException, ValidationException


def validate_stock_symbol(symbol: str, raise_exception: bool = True) -> bool:
    """
    Validate stock symbol format.
    
    Valid format: 4-digit number not starting with 0 (e.g., 2330, 1234)
    
    Args:
        symbol: Stock symbol to validate
        raise_exception: Whether to raise exception on invalid symbol
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        InvalidStockSymbolException: If symbol is invalid and raise_exception is True
    """
    if not symbol:
        if raise_exception:
            raise InvalidStockSymbolException(symbol or "")
        return False
    
    symbol = symbol.strip()
    
    if not re.match(VALID_STOCK_SYMBOL_PATTERN, symbol):
        if raise_exception:
            raise InvalidStockSymbolException(symbol)
        return False
    
    return True


def validate_stock_symbols(symbols: List[str]) -> List[str]:
    """
    Validate and filter a list of stock symbols.
    
    Returns only valid symbols, silently skips invalid ones.
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        List of valid stock symbols
    """
    valid_symbols = []
    for symbol in symbols:
        if validate_stock_symbol(symbol, raise_exception=False):
            valid_symbols.append(symbol.strip())
    return valid_symbols


def validate_market(market: str, raise_exception: bool = True) -> bool:
    """
    Validate market type.
    
    Args:
        market: Market type to validate
        raise_exception: Whether to raise exception on invalid market
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValidationException: If market is invalid and raise_exception is True
    """
    valid_markets = [m.value for m in Market]
    
    if market not in valid_markets:
        if raise_exception:
            raise ValidationException(
                f"Invalid market: {market}. Must be one of: {valid_markets}",
                field="market"
            )
        return False
    
    return True


def clean_stock_symbol(symbol: str) -> str:
    """
    Clean and normalize stock symbol.
    
    Args:
        symbol: Raw stock symbol
        
    Returns:
        Cleaned stock symbol
    """
    return symbol.strip().upper() if symbol else ""


def is_valid_price(price: float) -> bool:
    """Check if price is valid (positive number)."""
    return isinstance(price, (int, float)) and price > 0


def is_valid_volume(volume: int) -> bool:
    """Check if volume is valid (non-negative integer)."""
    return isinstance(volume, int) and volume >= 0


def validate_daily_data(data: dict) -> bool:
    """
    Validate daily stock data record.
    
    Args:
        data: Dictionary containing daily stock data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "stock_code", "trade_date", "open_price", 
        "high_price", "low_price", "close_price", "volume"
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            return False
    
    # Validate price fields
    price_fields = ["open_price", "high_price", "low_price", "close_price"]
    for field in price_fields:
        if not is_valid_price(data[field]):
            return False
    
    # Validate volume
    if not is_valid_volume(data["volume"]):
        return False
    
    return True
