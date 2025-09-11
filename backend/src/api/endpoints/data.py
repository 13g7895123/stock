"""Stock daily data API endpoints."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.daily_data_service import DailyDataService
from src.services.concurrent_stock_updater import ConcurrentStockUpdater
from src.models.stock import Stock
from src.api.endpoints.history import router as history_router

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/daily/{symbol}", response_model=Dict[str, Any])
async def get_daily_data_for_stock(
    symbol: str,
    force_update: bool = False,
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
        
        # Fetch and save daily data (with intelligent skip unless forced)
        result = await daily_data_service.get_daily_data_for_stock(symbol, force_update=force_update)
        
        if result.get("status") == "error":
            # Don't expose internal error details to client, but log them
            error_detail = result.get("error", "Unknown error occurred")
            logger.error(f"Daily data fetch failed for {symbol}: {error_detail}")
            
            # Return user-friendly error message
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch daily data for stock {symbol}. The broker data sources may be unavailable."
            )
        
        # Handle different result statuses
        if result.get("status") == "skipped":
            # Return skipped result
            response = {
                "status": "skipped",
                "stock_symbol": symbol,
                "message": f"Data for stock {symbol} is already up to date",
                "records_processed": result.get("records_processed", 0),
                "records_created": result.get("created", 0),
                "records_updated": result.get("updated", 0),
                "latest_date": result.get("latest_date"),
                "reason": result.get("reason", "Data already up to date"),
                "timestamp": result.get("timestamp"),
                "data_sources": "intelligent skip",
                "data_quality": "already_current"
            }
        else:
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


@router.post("/daily/batch-update", response_model=Dict[str, Any])
async def batch_update_daily_data(
    symbols: Optional[List[str]] = Body(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """批次爬取股票歷史資料 - Batch crawl daily data for multiple stocks using broker websites."""
    try:
        # If no symbols provided, get all active stocks from database
        if symbols is None:
            try:
                stocks = db.query(Stock).filter(Stock.is_active == True).all()
                symbols = [stock.symbol for stock in stocks]
                logger.info(f"Retrieved {len(symbols)} active stocks from database")
                
                if not symbols:
                    raise HTTPException(status_code=404, detail="No active stocks found in database")
                    
            except Exception as e:
                logger.error(f"Error retrieving stocks from database: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
        
        # Validate symbols format
        valid_symbols = []
        for symbol in symbols:
            if isinstance(symbol, str) and len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
                valid_symbols.append(symbol)
            else:
                logger.warning(f"Invalid symbol format: {symbol}, skipping")
        
        if not valid_symbols:
            raise HTTPException(status_code=400, detail="No valid stock symbols provided")
        
        logger.info(f"Starting batch daily data crawl for {len(valid_symbols)} stocks using broker websites")
        start_time = datetime.now()
        
        # Initialize counters
        successful_updates = 0
        failed_updates = 0
        total_records_processed = 0
        results = {}
        
        # Process each stock sequentially to avoid overwhelming broker servers
        for i, symbol in enumerate(valid_symbols):
            try:
                logger.info(f"Processing stock {i+1}/{len(valid_symbols)}: {symbol}")
                
                # Initialize daily data service for each stock
                daily_data_service = DailyDataService(db_session=db)
                
                # Fetch and save daily data using broker websites
                result = await daily_data_service.get_daily_data_for_stock(symbol)
                
                if result.get("status") == "success":
                    successful_updates += 1
                    total_records_processed += result.get("records_processed", 0)
                    results[symbol] = {
                        "status": "success",
                        "records_processed": result.get("records_processed", 0),
                        "records_created": result.get("created", 0),
                        "records_updated": result.get("updated", 0)
                    }
                    logger.info(f"Successfully processed {symbol}: {result.get('records_processed', 0)} records")
                else:
                    failed_updates += 1
                    results[symbol] = {
                        "status": "error",
                        "error": result.get("error", "Unknown error")
                    }
                    logger.error(f"Failed to process {symbol}: {result.get('error', 'Unknown error')}")
                
                # Small delay to avoid overwhelming broker servers
                if i < len(valid_symbols) - 1:  # Don't delay after last symbol
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_updates += 1
                results[symbol] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Prepare response
        response = {
            "status": "completed",
            "message": f"Batch update completed using broker websites crawling",
            "data_source": "8 broker websites (fubon-ebrokerdj, justdata.moneydj, etc.)",
            "summary": {
                "total_symbols": len(valid_symbols),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "total_records_processed": total_records_processed,
                "execution_time_seconds": round(execution_time, 2)
            },
            "results": results,
            "timestamp": end_time.isoformat()
        }
        
        logger.info(f"Batch daily data crawl completed: {successful_updates} success, {failed_updates} failed, {total_records_processed} total records, {execution_time:.2f}s")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch_update_daily_data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during batch daily data update: {str(e)}"
        )


@router.post("/daily/concurrent-batch-update", response_model=Dict[str, Any])
async def concurrent_batch_update_daily_data(
    symbols: Optional[List[str]] = Body(None),
    max_workers: int = Body(4),
    timeout_per_stock: float = Body(120.0),
    batch_size: int = Body(10),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    多執行續批次爬取股票歷史資料 - Concurrent batch crawl daily data with threading optimization.
    
    - **symbols**: 股票代號清單 (若為空則更新所有活躍股票)
    - **max_workers**: 最大併發執行緒數 (1-8)
    - **timeout_per_stock**: 每檔股票的超時時間(秒) 
    - **batch_size**: 批次大小 (每批處理的股票數量)
    """
    try:
        # Validate parameters
        max_workers = max(1, min(8, max_workers))  # Limit to 1-8 workers
        timeout_per_stock = max(30, min(300, timeout_per_stock))  # 30-300 seconds
        batch_size = max(1, min(50, batch_size))  # 1-50 per batch
        
        logger.info(f"Starting concurrent batch update with {max_workers} workers, timeout {timeout_per_stock}s, batch size {batch_size}")
        
        # If no symbols provided, get all active stocks from database
        if symbols is None:
            try:
                stocks = db.query(Stock).filter(Stock.is_active == True).all()
                symbols = [stock.stock_code for stock in stocks]
                logger.info(f"Retrieved {len(symbols)} active stocks from database")
                
                if not symbols:
                    raise HTTPException(status_code=404, detail="No active stocks found in database")
                    
            except Exception as e:
                logger.error(f"Error retrieving stocks from database: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
        
        # Validate symbols format
        valid_symbols = []
        for symbol in symbols:
            if symbol and len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
                valid_symbols.append(symbol)
            else:
                logger.warning(f"Invalid stock symbol: {symbol}")
        
        if not valid_symbols:
            raise HTTPException(status_code=400, detail="No valid stock symbols provided")
        
        logger.info(f"Processing {len(valid_symbols)} valid symbols with concurrent updater")
        
        # Create concurrent updater
        concurrent_updater = ConcurrentStockUpdater(
            db_session=db,
            max_workers=max_workers,
            timeout_per_stock=timeout_per_stock,
            batch_size=batch_size
        )
        
        # Execute concurrent update
        results = await concurrent_updater.update_stocks_concurrent(valid_symbols)
        
        # Prepare API response
        response = {
            "status": "completed",
            "message": f"Concurrent batch update completed with {max_workers} threads",
            "optimization": {
                "threading": True,
                "max_workers": max_workers,
                "timeout_per_stock": timeout_per_stock,
                "batch_size": batch_size,
                "execution_time": results["execution_time"]
            },
            "task_execution": {
                "task_id": results["task_id"],
                "tracking_enabled": True
            },
            "summary": {
                "total_stocks": results["total_stocks"],
                "successful_updates": results["successful_updates"],
                "skipped_updates": results["skipped_updates"],
                "failed_updates": results["failed_updates"],
                "total_records_processed": results["total_records_processed"],
                "total_records_created": results["total_records_created"],
                "total_records_updated": results["total_records_updated"],
                "success_rate": round((results["successful_updates"] / results["total_stocks"] * 100), 2) if results["total_stocks"] > 0 else 0,
                "skip_rate": round((results["skipped_updates"] / results["total_stocks"] * 100), 2) if results["total_stocks"] > 0 else 0,
                "average_time_per_stock": round((results["execution_time"] / results["total_stocks"]), 2) if results["total_stocks"] > 0 else 0
            },
            "successful_stocks": results["successful_stocks"],
            "skipped_stocks": results["skipped_stocks"],
            "failed_stocks": results["failed_stocks"],
            "detailed_results": results["detailed_results"] if len(results["detailed_results"]) <= 20 else results["detailed_results"][:20],  # Limit response size
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Concurrent batch update completed: {results['successful_updates']} success, {results['failed_updates']} failed, {results['execution_time']:.1f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in concurrent batch update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during concurrent batch update: {str(e)}"
        )


# Include history router
router.include_router(history_router, tags=["Stock History"])
