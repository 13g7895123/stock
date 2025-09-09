"""Celery application configuration."""
from celery import Celery
from typing import Any

from src.core.config import settings

# Create Celery instance
celery_app = Celery(
    "stock_analysis",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.celery_app.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "src.celery_app.tasks.data_collection.*": {"queue": "data_collection"},
        "src.celery_app.tasks.analysis.*": {"queue": "analysis"},
        "src.celery_app.tasks.notifications.*": {"queue": "notifications"},
    },
    beat_schedule={
        "update-market-data": {
            "task": "src.celery_app.tasks.data_collection.update_market_data",
            "schedule": 300.0,  # Run every 5 minutes during market hours
        },
        "run-technical-analysis": {
            "task": "src.celery_app.tasks.analysis.run_technical_analysis",
            "schedule": 900.0,  # Run every 15 minutes
        },
    } if settings.ENABLE_SCHEDULED_TASKS else {},
)


# Test task
@celery_app.task
def test_celery() -> str:
    """Test Celery connection."""
    return "Celery is working!"


def create_celery_app() -> Celery:
    """Create Celery app factory."""
    return celery_app