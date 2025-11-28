"""Main FastAPI application.

股票分析系統後端入口點。
採用模組化架構，清晰分離關注點。
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.api.router import register_routers
from src.api.exception_handlers import register_exception_handlers
from src.core.config import settings
from src.core.database import create_tables


def setup_logging() -> logging.Logger:
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if settings.LOG_FILE_PATH:
        Path(settings.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(settings.LOG_FILE_PATH))
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )
    
    return logging.getLogger(__name__)


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    # === Startup ===
    logger.info("Starting Stock Analysis System...")
    
    # Create required directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    create_tables()
    logger.info("Database tables created/verified")
    
    logger.info(f"Application started on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # === Shutdown ===
    logger.info("Shutting down Stock Analysis System...")


def create_application() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="股票分析系統 - 提供技術分析、資料爬取與選股功能",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Configure trusted hosts
    allowed_hosts = ["*"] if settings.DEBUG else [
        settings.HOST,
        "localhost",
        "127.0.0.1",
        f"localhost:{settings.PORT}"
    ]
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    
    # Register routes and exception handlers
    register_routers(application)
    register_exception_handlers(application)
    
    return application


# Create application instance
app = create_application()


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
    )