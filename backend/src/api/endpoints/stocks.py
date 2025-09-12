"""Stock data endpoints."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.core.database import get_db
from src.core.config import settings
from src.models.stock import Stock
from src.celery_app.tasks.data_collection import update_market_data, fetch_historical_data
from src.celery_app.tasks.analysis import run_technical_analysis, generate_signals

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list")
async def get_stock_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="頁數"),
    limit: int = Query(50, ge=1, le=1000, description="每頁筆數"),
    market: Optional[str] = Query(None, description="市場篩選 (TSE/TPEx)"),
    search: Optional[str] = Query(None, description="搜尋股票代號或名稱")
) -> Dict[str, Any]:
    """從資料庫獲取股票列表"""
    try:
        # 建立基礎查詢
        query = db.query(Stock).filter(Stock.is_active == True)
        
        # 市場篩選
        if market:
            query = query.filter(Stock.market == market)
            
        # 搜尋功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Stock.symbol.ilike(search_pattern)) | 
                (Stock.name.ilike(search_pattern))
            )
        
        # 計算總數
        total = query.count()
        
        # 分頁
        offset = (page - 1) * limit
        stocks = query.order_by(Stock.symbol).offset(offset).limit(limit).all()
        
        # 格式化回傳資料
        stock_list = []
        for stock in stocks:
            stock_list.append({
                "code": stock.symbol,
                "name": stock.name,
                "market": stock.market,
                "industry": stock.industry or "未分類",
                "price": 0.00,  # 需要從其他來源獲取即時價格
                "change": 0.0,  # 需要計算漲跌幅
                "dataStatus": "complete",
                "lastUpdate": "即時"
            })
        
        return {
            "status": "success",
            "stocks": stock_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "has_next": page * limit < total,
                "has_previous": page > 1
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stock list: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取股票列表失敗")


@router.get("/symbols")
async def get_available_symbols() -> Dict[str, Any]:
    """Get list of available stock symbols."""
    return {
        "symbols": settings.DEFAULT_STOCK_SYMBOLS,
        "count": len(settings.DEFAULT_STOCK_SYMBOLS),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{symbol}/current")
async def get_current_price(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current price for a stock symbol."""
    # TODO: Implement actual price retrieval from database
    logger.info(f"Getting current price for {symbol}")
    
    # Placeholder response
    return {
        "symbol": symbol.upper(),
        "price": 0.0,  # Placeholder
        "change": 0.0,  # Placeholder
        "change_percent": 0.0,  # Placeholder
        "volume": 0,  # Placeholder
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Price data not implemented yet"
    }


@router.get("/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    start_date: date = Query(..., description="Start date for historical data"),
    end_date: date = Query(..., description="End date for historical data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get historical price data for a stock symbol."""
    logger.info(f"Getting historical data for {symbol} from {start_date} to {end_date}")
    
    # TODO: Implement actual historical data retrieval from database
    
    # Placeholder response
    return {
        "symbol": symbol.upper(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data": [],  # Placeholder for actual data
        "count": 0,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Historical data not implemented yet"
    }


@router.post("/{symbol}/update")
async def trigger_data_update(
    symbol: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Trigger data update for a specific symbol."""
    logger.info(f"Triggering data update for {symbol}")
    
    # Start background task
    task = update_market_data.delay([symbol.upper()])
    
    return {
        "message": f"Data update triggered for {symbol.upper()}",
        "task_id": task.id,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/update-all")
async def trigger_all_data_update(
    symbols: Optional[List[str]] = Body(default=None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger data update for all or specified symbols."""
    if symbols is None:
        # 從資料庫查詢所有啟用的股票
        try:
            stocks = db.query(Stock).filter(Stock.is_active == True).all()
            symbols = [stock.symbol for stock in stocks]
            logger.info(f"Retrieved {len(symbols)} active stocks from database")
            
            if not symbols:
                raise HTTPException(status_code=404, detail="No active stocks found in database")
                
        except Exception as e:
            logger.error(f"Error retrieving stocks from database: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
    
    symbols = [s.upper() for s in symbols]
    logger.info(f"Triggering data update for {len(symbols)} symbols: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")
    
    # Start background task
    task = update_market_data.delay(symbols)
    
    return {
        "message": f"Data update triggered for {len(symbols)} symbols from database",
        "symbols": symbols,
        "task_id": task.id,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{symbol}/analysis")
async def get_technical_analysis(
    symbol: str,
    indicators: Optional[List[str]] = Query(None, description="Technical indicators to include"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get technical analysis for a stock symbol."""
    logger.info(f"Getting technical analysis for {symbol}")
    
    # TODO: Implement actual technical analysis retrieval from database
    
    available_indicators = ["SMA", "EMA", "RSI", "MACD", "BB", "STOCH"]
    if indicators is None:
        indicators = available_indicators[:3]  # Default to first 3
    
    # Placeholder response
    analysis_data = {}
    for indicator in indicators:
        if indicator in available_indicators:
            analysis_data[indicator] = {
                "current_value": 0.0,  # Placeholder
                "signal": "NEUTRAL",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    return {
        "symbol": symbol.upper(),
        "indicators": analysis_data,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Technical analysis not implemented yet"
    }


@router.post("/{symbol}/analyze")
async def trigger_technical_analysis(
    symbol: str,
    indicators: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """Trigger technical analysis for a specific symbol."""
    logger.info(f"Triggering technical analysis for {symbol}")
    
    # Start background task
    task = run_technical_analysis.delay([symbol.upper()], indicators)
    
    return {
        "message": f"Technical analysis triggered for {symbol.upper()}",
        "task_id": task.id,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{symbol}/signals")
async def get_trading_signals(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get trading signals for a stock symbol."""
    logger.info(f"Getting trading signals for {symbol}")
    
    # TODO: Implement actual signal retrieval from database
    
    # Placeholder response
    return {
        "symbol": symbol.upper(),
        "signal": "HOLD",
        "strength": 0.0,
        "confidence": 0.0,
        "indicators_used": ["SMA", "RSI", "MACD"],
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Trading signals not implemented yet"
    }


@router.post("/signals/generate")
async def trigger_signal_generation(
    symbols: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """Trigger signal generation for specified symbols."""
    if symbols is None:
        symbols = settings.DEFAULT_STOCK_SYMBOLS
    
    symbols = [s.upper() for s in symbols]
    logger.info(f"Triggering signal generation for symbols: {symbols}")
    
    # Start background task
    task = generate_signals.delay(symbols)
    
    return {
        "message": f"Signal generation triggered for {len(symbols)} symbols",
        "symbols": symbols,
        "task_id": task.id,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat()
    }