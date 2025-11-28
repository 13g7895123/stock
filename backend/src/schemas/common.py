"""Common Pydantic schemas.

定義通用的請求和回應模型。
"""
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


# === Pagination Schemas ===

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="頁數")
    limit: int = Field(default=50, ge=1, le=1000, description="每頁筆數")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.limit


class PaginationInfo(BaseModel):
    """Pagination info for responses."""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def from_params(cls, params: PaginationParams, total: int) -> "PaginationInfo":
        """Create from pagination params."""
        total_pages = (total + params.limit - 1) // params.limit if params.limit > 0 else 0
        return cls(
            page=params.page,
            limit=params.limit,
            total=total,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )


# === Generic Response Schemas ===

class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: ErrorDetail
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""
    success: bool = True
    data: List[T]
    pagination: PaginationInfo
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# === Task Schemas ===

class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    task_name: str
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class BatchOperationSummary(BaseModel):
    """Summary for batch operations."""
    total: int = Field(..., ge=0)
    successful: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    skipped: int = Field(default=0, ge=0)
    execution_time_seconds: float = Field(..., ge=0)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return round((self.successful / self.total) * 100, 2) if self.total > 0 else 0.0


# === Health Check Schemas ===

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    components: Optional[Dict[str, Any]] = None


class ComponentHealth(BaseModel):
    """Individual component health."""
    name: str
    status: str
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
