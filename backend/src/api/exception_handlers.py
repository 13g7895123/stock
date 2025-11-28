"""Exception handlers for FastAPI.

集中管理所有例外處理器。
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions import BaseAppException
from src.core.config import settings


logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Handle application-specific exceptions."""
    logger.warning(f"Application exception: {exc.code} - {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # In debug mode, include error details
    detail = str(exc) if settings.DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": detail,
                "details": {}
            }
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers to the FastAPI app."""
    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
