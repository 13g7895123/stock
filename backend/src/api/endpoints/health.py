"""Health check endpoints."""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.database import get_db
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check including database connectivity."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    # Database health check
    try:
        db.execute(text("SELECT 1"))
        health_data["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_data["status"] = "unhealthy"
    
    # Redis health check (if available)
    try:
        # TODO: Add Redis connection check
        health_data["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection not implemented yet"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_data["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    # Celery health check
    try:
        # TODO: Add Celery health check
        health_data["checks"]["celery"] = {
            "status": "healthy",
            "message": "Celery health check not implemented yet"
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        health_data["checks"]["celery"] = {
            "status": "unhealthy",
            "message": f"Celery health check failed: {str(e)}"
        }
    
    # Return 503 if any checks failed
    if health_data["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check for Kubernetes probes."""
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes probes."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }