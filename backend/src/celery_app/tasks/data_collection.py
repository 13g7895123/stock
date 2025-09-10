"""Data collection tasks for stock market data."""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from celery import current_task
from src.celery_app.celery_app import celery_app
from src.core.config import settings
from src.core.database import get_db
from src.services.stock_data_updater import StockDataUpdater

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def update_market_data(self, symbols: List[str] = None, force_full_update: bool = False) -> Dict[str, Any]:
    """
    Update market data for specified symbols using real stock data fetcher.
    
    Args:
        symbols: List of stock symbols to update
        force_full_update: Whether to perform full update instead of incremental
        
    Returns:
        Dictionary with update results
    """
    if symbols is None:
        symbols = settings.DEFAULT_STOCK_SYMBOLS
    
    logger.info(f"Starting REAL market data update for {len(symbols)} symbols")
    
    try:
        # Get database session
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            # Initialize stock data updater
            updater = StockDataUpdater(db_session)
            
            # Update task progress
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 0, 
                    "total": len(symbols), 
                    "status": "Initializing real data update..."
                }
            )
            
            # Run async update function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use the real stock data updater
                result = loop.run_until_complete(
                    updater.update_multiple_stocks(
                        symbols=symbols,
                        days_back=365,  # Get 1 year of data
                        force_full_update=force_full_update
                    )
                )
                
                logger.info(f"Market data update completed: {result.get('success_count', 0)} success, {result.get('error_count', 0)} errors")
                
                # Final progress update
                current_task.update_state(
                    state="PROGRESS", 
                    meta={
                        "current": len(symbols),
                        "total": len(symbols),
                        "status": f"Completed: {result.get('total_records_updated', 0)} records updated"
                    }
                )
                
                return result
                
            finally:
                loop.close()
                
        finally:
            # Close database session
            db_session.close()
        
    except Exception as exc:
        logger.error(f"Error updating market data: {str(exc)}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(exc), "timestamp": datetime.utcnow().isoformat()}
        )
        raise


@celery_app.task(bind=True)
def fetch_historical_data(
    self, symbol: str, start_date: str, end_date: str, force_full_update: bool = False
) -> Dict[str, Any]:
    """
    Fetch historical data for a specific symbol using real data fetcher.
    
    Args:
        symbol: Stock symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        force_full_update: Whether to force full update
        
    Returns:
        Dictionary with historical data
    """
    logger.info(f"Fetching REAL historical data for {symbol} from {start_date} to {end_date}")
    
    try:
        # Get database session
        db_gen = get_db()
        db_session = next(db_gen)
        
        try:
            current_task.update_state(
                state="PROGRESS",
                meta={"status": f"Fetching real historical data for {symbol}"}
            )
            
            # Initialize stock data updater
            updater = StockDataUpdater(db_session)
            
            # Convert string dates to date objects
            from datetime import datetime as dt
            start_date_obj = dt.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = dt.strptime(end_date, '%Y-%m-%d').date()
            
            # Calculate days back from end date to start date
            days_back = (end_date_obj - start_date_obj).days
            
            # Run async update function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    updater.update_stock_data(
                        symbol=symbol,
                        days_back=max(days_back, 365),  # At least 1 year
                        force_full_update=force_full_update
                    )
                )
                
                logger.info(f"Historical data fetch completed for {symbol}: {result.get('records_updated', 0)} records")
                return result
                
            finally:
                loop.close()
                
        finally:
            # Close database session
            db_session.close()
        
    except Exception as exc:
        logger.error(f"Error fetching historical data for {symbol}: {str(exc)}")
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(exc), "symbol": symbol}
        )
        raise


@celery_app.task
def cleanup_old_data(days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Clean up old market data.
    
    Args:
        days_to_keep: Number of days of data to keep
        
    Returns:
        Cleanup results
    """
    logger.info(f"Starting cleanup of data older than {days_to_keep} days")
    
    try:
        # TODO: Implement actual cleanup logic
        # This is a placeholder for the actual implementation
        
        result = {
            "status": "completed",
            "days_to_keep": days_to_keep,
            "records_deleted": 0,  # Placeholder
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Data cleanup completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Error during data cleanup: {str(exc)}")
        raise