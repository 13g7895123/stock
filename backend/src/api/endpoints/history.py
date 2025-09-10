"""股票歷史資料查詢API端點

提供股票歷史資料查詢功能的REST API接口，支援：
- 基本資料查詢：GET /api/v1/data/history/{symbol}
- 日期範圍篩選：?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
- 分頁功能：?page=1&limit=50
- 排序功能：?sort_by=trade_date&sort_order=desc
- 統計資訊：GET /api/v1/data/history/{symbol}/stats
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.stock_history_service import StockHistoryService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_stock_history_service(db: Session = Depends(get_db)) -> StockHistoryService:
    """依賴注入：取得股票歷史資料服務實例"""
    return StockHistoryService(db_session=db)


@router.get("/history/{symbol}", response_model=Dict[str, Any])
async def get_stock_history(
    symbol: str,
    start_date: Optional[str] = Query(
        None, 
        description="開始日期 (YYYY-MM-DD格式)",
        example="2024-01-01"
    ),
    end_date: Optional[str] = Query(
        None, 
        description="結束日期 (YYYY-MM-DD格式)",
        example="2024-12-31"
    ),
    page: int = Query(
        1, 
        ge=1, 
        description="頁數，從1開始",
        example=1
    ),
    limit: int = Query(
        50, 
        ge=1, 
        le=1000, 
        description="每頁資料筆數，最多1000筆",
        example=50
    ),
    sort_by: str = Query(
        "trade_date", 
        description="排序欄位",
        example="trade_date"
    ),
    sort_order: str = Query(
        "desc", 
        description="排序方向 (asc/desc)",
        example="desc"
    ),
    history_service: StockHistoryService = Depends(get_stock_history_service)
) -> Dict[str, Any]:
    """查詢特定股票的歷史交易資料
    
    此API端點允許查詢指定股票的歷史交易資料，支援多種篩選和排序選項。
    
    **支援的排序欄位：**
    - trade_date: 交易日期
    - close_price: 收盤價
    - volume: 成交量
    - high_price: 最高價
    - low_price: 最低價
    
    **回傳資料格式：**
    - status: 查詢狀態
    - stock_symbol: 股票代號
    - data: 歷史資料陣列
    - total_records: 總筆數
    - pagination: 分頁資訊
    - query_params: 查詢參數
    
    **範例用法：**
    - 查詢所有資料：`/api/v1/data/history/2330`
    - 日期範圍查詢：`/api/v1/data/history/2330?start_date=2024-01-01&end_date=2024-12-31`
    - 分頁查詢：`/api/v1/data/history/2330?page=2&limit=100`
    - 排序查詢：`/api/v1/data/history/2330?sort_by=close_price&sort_order=asc`
    """
    try:
        logger.info(f"Received history request for stock {symbol} with params: "
                   f"start_date={start_date}, end_date={end_date}, page={page}, "
                   f"limit={limit}, sort_by={sort_by}, sort_order={sort_order}")
        
        # 呼叫服務層處理業務邏輯
        result = history_service.get_stock_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(f"Successfully retrieved history for stock {symbol}: "
                   f"{result['total_records']} total records, "
                   f"{len(result['data'])} records in current page")
        
        return result
        
    except ValueError as e:
        # 參數驗證錯誤
        logger.warning(f"Invalid parameters for stock history request {symbol}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # 其他系統錯誤
        logger.error(f"Unexpected error retrieving history for stock {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving stock history for {symbol}"
        )


@router.get("/history/{symbol}/stats", response_model=Dict[str, Any])
async def get_stock_statistics(
    symbol: str,
    history_service: StockHistoryService = Depends(get_stock_history_service)
) -> Dict[str, Any]:
    """取得特定股票的統計資訊
    
    提供股票歷史資料的統計摘要，包含：
    - 資料總筆數
    - 日期範圍（最早到最新）
    - 近期價格範圍（最近30天）
    
    **回傳資料格式：**
    - stock_symbol: 股票代號
    - total_records: 總資料筆數
    - date_range: 日期範圍資訊
    - price_range: 價格範圍資訊（近30天）
    """
    try:
        logger.info(f"Received statistics request for stock {symbol}")
        
        # 呼叫服務層取得統計資訊
        result = history_service.get_stock_statistics(symbol)
        
        logger.info(f"Successfully retrieved statistics for stock {symbol}: "
                   f"{result['total_records']} total records")
        
        return result
        
    except ValueError as e:
        # 參數驗證錯誤
        logger.warning(f"Invalid stock symbol for statistics request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # 其他系統錯誤
        logger.error(f"Unexpected error retrieving statistics for stock {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving statistics for {symbol}"
        )


@router.get("/history/{symbol}/latest-date", response_model=Dict[str, Any])
async def get_latest_trade_date(
    symbol: str,
    history_service: StockHistoryService = Depends(get_stock_history_service)
) -> Dict[str, Any]:
    """取得特定股票的最新交易日期
    
    此端點回傳指定股票在系統中最新的交易日期。
    用於檢查資料是否為最新，或判斷是否需要更新資料。
    
    **回傳資料格式：**
    - stock_symbol: 股票代號
    - latest_trade_date: 最新交易日期 (YYYY-MM-DD)
    - has_data: 是否有資料
    - message: 說明訊息
    """
    try:
        logger.info(f"Received latest date request for stock {symbol}")
        
        # 取得最新交易日期
        latest_date = history_service.get_latest_trade_date(symbol)
        
        if latest_date:
            date_str = latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)
            message = f"Latest trade date for stock {symbol} is {date_str}"
            logger.info(f"Found latest trade date for {symbol}: {date_str}")
        else:
            date_str = None
            message = f"No trade data found for stock {symbol}"
            logger.info(f"No trade data found for stock {symbol}")
        
        return {
            "stock_symbol": symbol,
            "latest_trade_date": date_str,
            "has_data": latest_date is not None,
            "message": message
        }
        
    except ValueError as e:
        # 參數驗證錯誤
        logger.warning(f"Invalid stock symbol for latest date request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # 其他系統錯誤
        logger.error(f"Unexpected error retrieving latest date for stock {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving latest date for {symbol}"
        )