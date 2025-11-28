"""Standardized API response utilities.

提供統一的 API 回應格式，確保所有端點回傳一致的結構。
"""
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=1000, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationInfo":
        """Create pagination info from parameters."""
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
                "timestamp": "2024-01-01T00:00:00"
            }
        }


class PaginatedResponse(ApiResponse[List[T]], Generic[T]):
    """Paginated API response."""
    pagination: Optional[PaginationInfo] = None


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error API response."""
    success: bool = Field(default=False)
    error: ErrorDetail
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# === Response Builder Functions ===

def success_response(
    data: Any = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Build a success response."""
    response = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def paginated_response(
    data: List[Any],
    page: int,
    limit: int,
    total: int,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Build a paginated response."""
    response = success_response(data=data, message=message)
    response["pagination"] = PaginationInfo.create(page, limit, total).model_dump()
    return response


def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build an error response."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# === Common Response Schemas ===

class TaskResponse(BaseModel):
    """Task execution response."""
    status: str = Field(..., description="Task status")
    task_id: Optional[str] = Field(None, description="Task ID for tracking")
    message: str = Field(..., description="Task message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchOperationSummary(BaseModel):
    """Summary for batch operations."""
    total: int = Field(..., ge=0, description="Total items processed")
    successful: int = Field(..., ge=0, description="Successfully processed items")
    failed: int = Field(..., ge=0, description="Failed items")
    skipped: int = Field(default=0, ge=0, description="Skipped items")
    execution_time_seconds: float = Field(..., ge=0, description="Execution time in seconds")

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return round((self.successful / self.total) * 100, 2)


class StockOperationResult(BaseModel):
    """Result of a single stock operation."""
    stock_code: str
    status: str
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    error: Optional[str] = None
