"""Stock synchronization API endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.stock_list_service import StockListService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stocks/sync", response_model=Dict[str, Any])
async def sync_stock_list(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """同步股票列表 - Synchronize stock list from TSE and TPEx."""
    try:
        stock_service = StockListService(db_session=db)
        
        # 執行同步
        result = await stock_service.sync_all_stocks()
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sync_stock_list: {e}")
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.get("/stocks/count", response_model=Dict[str, Any])
async def get_stock_counts(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """取得股票統計 - Get stock counts by market."""
    try:
        stock_service = StockListService(db_session=db)
        
        market_counts = stock_service.get_stock_count_by_market()
        total_count = sum(market_counts.values())
        
        return {
            "total": total_count,
            "by_market": market_counts,
            "markets": list(market_counts.keys())
        }
        
    except Exception as e:
        logger.error(f"Error in get_stock_counts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stock counts: {str(e)}")


@router.get("/stocks/validate/{symbol}")
async def validate_stock_symbol(
    symbol: str,
) -> Dict[str, Any]:
    """驗證股票代號格式 - Validate stock symbol format."""
    try:
        stock_service = StockListService()
        
        # 建立測試股票資料
        test_stock = {
            "symbol": symbol,
            "name": "Test Stock",
            "market": "TSE"
        }
        
        is_valid = stock_service.validate_stock_data(test_stock)
        
        return {
            "symbol": symbol,
            "is_valid": is_valid,
            "is_four_digit": len(symbol) == 4,
            "is_numeric": symbol.isdigit(),
            "starts_with_zero": symbol.startswith("0") if symbol else False,
            "message": "Valid stock symbol" if is_valid else "Invalid stock symbol format"
        }
        
    except Exception as e:
        logger.error(f"Error in validate_stock_symbol: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/stocks/crawl", response_model=Dict[str, Any])
async def crawl_stock_list(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """爬取股票列表並更新資料庫 - Crawl stock list and update database."""
    try:
        stock_service = StockListService(db_session=db)
        
        # 執行股票列表爬取和同步
        logger.info("Starting stock list crawl and database update")
        result = await stock_service.sync_all_stocks()
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # 確保回應包含資料庫更新資訊
        response = {
            "status": result.get("status", "success"),
            "message": result.get("message", "Stock list crawled and database updated"),
            "total_stocks": result.get("total_stocks", 0),
            "tse_stocks": result.get("tse_stocks", 0),
            "tpex_stocks": result.get("tpex_stocks", 0),
            "filtered_stocks": result.get("filtered_stocks", result.get("total_stocks", 0)),
            "new_stocks": result.get("new_stocks", 0),
            "updated_stocks": result.get("updated_stocks", 0),
            "database_updated": True,
            "timestamp": result.get("timestamp"),
            "last_update_time": result.get("timestamp")
        }
        
        # 包含錯誤資訊（如果有的話）
        if "errors" in result:
            response["errors"] = result["errors"]
        
        logger.info(f"Stock crawl completed: {response['total_stocks']} total stocks processed")
        return response
        
    except Exception as e:
        logger.error(f"Error in crawl_stock_list: {e}")
        raise HTTPException(status_code=500, detail=f"Stock crawl failed: {str(e)}")