"""Main FastAPI application."""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.endpoints import health, stocks, stock_sync
from src.core.config import settings
from src.core.database import create_tables

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE_PATH) if settings.LOG_FILE_PATH else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Stock Analysis System...")
    
    # Create upload directory
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    logger.info(f"Application started successfully on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stock Analysis System...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive stock analysis system with technical analysis capabilities",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else [
        settings.HOST, 
        "localhost", 
        "127.0.0.1", 
        f"localhost:{settings.PORT}"
    ],
)

# Include routers
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health Check"]
)

app.include_router(
    stocks.router,
    prefix="/api/v1/stocks",
    tags=["Stocks"]
)

app.include_router(
    stock_sync.router,
    prefix="/api/v1/sync",
    tags=["Stock Synchronization"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc),
            "type": "internal_server_error"
        }
    )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
    )