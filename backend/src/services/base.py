"""Base service class with common functionality.

提供所有 Service 類別的共用功能，減少程式碼重複。
"""
import logging
from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import httpx
from sqlalchemy.orm import Session

from src.core.constants import DEFAULT_HTTP_TIMEOUT
from src.core.exceptions import DatabaseException, ExternalServiceException


logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT")


class BaseService(ABC):
    """Abstract base class for all services."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize service with optional database session."""
        self._db_session = db_session
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def db(self) -> Session:
        """Get database session with validation."""
        if self._db_session is None:
            raise DatabaseException("Database session not provided")
        return self._db_session

    @property
    def has_db(self) -> bool:
        """Check if database session is available."""
        return self._db_session is not None


class BaseHttpService(BaseService):
    """Base class for services that make HTTP requests."""

    def __init__(
        self,
        db_session: Optional[Session] = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT
    ):
        """Initialize HTTP service."""
        super().__init__(db_session)
        self._timeout = httpx.Timeout(timeout)
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        service_name: str = "external"
    ) -> httpx.Response:
        """Make HTTP request with error handling."""
        request_headers = {**self._default_headers, **(headers or {})}
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=request_headers,
                    json=json_data
                )
                response.raise_for_status()
                return response
                
        except httpx.TimeoutException:
            self._logger.error(f"Timeout while requesting {url}")
            raise ExternalServiceException(service_name, f"Request timeout: {url}")
        except httpx.HTTPStatusError as e:
            self._logger.error(f"HTTP error {e.response.status_code} from {url}")
            raise ExternalServiceException(service_name, f"HTTP {e.response.status_code}: {url}")
        except httpx.RequestError as e:
            self._logger.error(f"Request error for {url}: {e}")
            raise ExternalServiceException(service_name, f"Request failed: {str(e)}")

    async def _get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        service_name: str = "external"
    ) -> Dict[str, Any]:
        """Make GET request and return JSON response."""
        response = await self._make_request("GET", url, params=params, service_name=service_name)
        return response.json()

    async def _get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        service_name: str = "external"
    ) -> str:
        """Make GET request and return text response."""
        response = await self._make_request("GET", url, params=params, service_name=service_name)
        return response.text


class BaseCrudService(BaseService, Generic[ModelT]):
    """Base class for CRUD services."""

    def __init__(self, db_session: Session, model: Type[ModelT]):
        """Initialize CRUD service."""
        super().__init__(db_session)
        self._model = model

    def get_by_id(self, id: int) -> Optional[ModelT]:
        """Get record by ID."""
        return self.db.query(self._model).filter(self._model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelT]:
        """Get all records with pagination."""
        return self.db.query(self._model).offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelT:
        """Create new record."""
        db_obj = self._model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelT]:
        """Update record by ID."""
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """Delete record by ID."""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """Count total records."""
        return self.db.query(self._model).count()
