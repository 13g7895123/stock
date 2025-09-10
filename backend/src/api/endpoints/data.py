"""Data management API endpoints."""

from fastapi import APIRouter

from .history import router as history_router

router = APIRouter()

# Include history router
router.include_router(
    history_router,
    tags=["Stock History Data"]
)