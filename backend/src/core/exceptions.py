"""Custom exception classes for the application.

提供統一的例外處理機制，使錯誤處理更加一致且易於維護。
"""
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


# === Database Exceptions ===

class DatabaseException(BaseAppException):
    """Database related exceptions."""
    
    def __init__(self, message: str = "Database error occurred", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", status_code=500, details=details)


class RecordNotFoundException(BaseAppException):
    """Record not found in database."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class DuplicateRecordException(BaseAppException):
    """Duplicate record exception."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} already exists: {identifier}",
            code="DUPLICATE_RECORD",
            status_code=409,
            details={"resource": resource, "identifier": str(identifier)}
        )


# === Validation Exceptions ===

class ValidationException(BaseAppException):
    """Validation error exception."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        _details = details or {}
        if field:
            _details["field"] = field
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=_details)


class InvalidStockSymbolException(ValidationException):
    """Invalid stock symbol exception."""
    
    def __init__(self, symbol: str):
        super().__init__(
            message=f"Invalid stock symbol: {symbol}. Must be 4-digit number not starting with 0.",
            field="symbol",
            details={"symbol": symbol}
        )


# === External Service Exceptions ===

class ExternalServiceException(BaseAppException):
    """External service (API) error exception."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        _details = details or {}
        _details["service"] = service
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=_details
        )


class BrokerServiceException(ExternalServiceException):
    """Broker service error exception."""
    
    def __init__(self, broker_url: str, message: str):
        super().__init__(
            service="broker",
            message=message,
            details={"broker_url": broker_url}
        )


class TWseApiException(ExternalServiceException):
    """TWSE API error exception."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None):
        super().__init__(
            service="TWSE",
            message=message,
            details={"endpoint": endpoint} if endpoint else None
        )


class TpexApiException(ExternalServiceException):
    """TPEx API error exception."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None):
        super().__init__(
            service="TPEx",
            message=message,
            details={"endpoint": endpoint} if endpoint else None
        )


# === Business Logic Exceptions ===

class BusinessLogicException(BaseAppException):
    """Business logic error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="BUSINESS_ERROR", status_code=400, details=details)


class DataNotAvailableException(BusinessLogicException):
    """Data not available exception."""
    
    def __init__(self, stock_code: str, reason: str = "No data available"):
        super().__init__(
            message=f"Data not available for {stock_code}: {reason}",
            details={"stock_code": stock_code, "reason": reason}
        )


class RateLimitException(BaseAppException):
    """Rate limit exceeded exception."""
    
    def __init__(self, retry_after: Optional[int] = None):
        details = {"retry_after_seconds": retry_after} if retry_after else None
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )
