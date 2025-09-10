"""Data management API endpoints."""

from fastapi import APIRouter

from .history import router as history_router

router = APIRouter()

# Include history router
router.include_router(
    history_router,
    tags=["Stock History Data"]
)
"""Stock daily data API endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.daily_data_service import DailyDataService
from src.api.endpoints.history import router as history_router

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/daily/{symbol}", response_model=Dict[str, Any])
async def get_daily_data_for_stock(
    symbol: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """爬取並更新單一股票還原日線資料 - Fetch and update daily data for a single stock."""
    try:
        # Validate symbol format
        if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stock symbol: {symbol}. Must be 4-digit number not starting with 0."
            )
        
        logger.info(f"Starting daily data fetch for stock {symbol}")
        
        # Initialize daily data service
        daily_data_service = DailyDataService(db_session=db)
        
        # Fetch and save daily data
        result = await daily_data_service.get_daily_data_for_stock(symbol)
        
        if result.get("status") == "error":
            # Don't expose internal error details to client, but log them
            error_detail = result.get("error", "Unknown error occurred")
            logger.error(f"Daily data fetch failed for {symbol}: {error_detail}")
            
            # Return user-friendly error message
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch daily data for stock {symbol}. The broker data sources may be unavailable."
            )
        
        # Return successful result
        response = {
            "status": result.get("status", "success"),
            "stock_symbol": symbol,
            "message": f"Successfully processed daily data for stock {symbol}",
            "records_processed": result.get("records_processed", 0),
            "records_created": result.get("created", 0),
            "records_updated": result.get("updated", 0),
            "timestamp": result.get("timestamp"),
            "data_sources": "8 broker websites",
            "data_quality": "adjusted_daily_prices"
        }
        
        logger.info(f"Daily data fetch completed for {symbol}: {response['records_processed']} records processed")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_daily_data_for_stock for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing daily data for {symbol}"
        )


@router.get("/daily/{symbol}/latest", response_model=Dict[str, Any])
async def get_latest_data_date(
    symbol: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """取得股票最新資料日期 - Get latest data date for a stock."""
    try:
        # Validate symbol format
        if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stock symbol: {symbol}. Must be 4-digit number not starting with 0."
            )
        
        logger.info(f"Getting latest data date for stock {symbol}")
        
        # Initialize daily data service
        daily_data_service = DailyDataService(db_session=db)
        
        # Get latest date
        latest_date = daily_data_service.get_latest_date_from_database(symbol)
        
        response = {
            "stock_symbol": symbol,
            "latest_date": latest_date.isoformat() if latest_date else None,
            "has_data": latest_date is not None,
            "message": f"Latest data date for stock {symbol}" + (
                f" is {latest_date.date()}" if latest_date 
                else " - no data found"
            )
        }
        
        logger.info(f"Latest data date query completed for {symbol}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error getting latest data date for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest data date for stock {symbol}"
        )


# Include history router
router.include_router(history_router, tags=["Stock History"])
