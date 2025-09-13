"""均線計算API端點"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.services.moving_averages_service import MovingAveragesService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic 請求模型
class MovingAveragesCalculateRequest(BaseModel):
    """均線計算請求模型"""
    stock_codes: Optional[List[str]] = Field(
        None, 
        description="股票代碼清單，為空則計算所有有資料的股票",
        example=["2330", "2317", "2454"]
    )
    periods: List[int] = Field(
        default=[5, 10, 20, 60, 120, 240],
        description="均線週期列表", 
        example=[5, 10, 20, 60]
    )
    force_recalculate: bool = Field(
        default=False,
        description="是否強制重新計算"
    )


class MovingAveragesAsyncRequest(BaseModel):
    """非同步均線計算請求模型"""
    stock_codes: Optional[List[str]] = Field(
        None,
        description="股票代碼清單，為空則計算所有有資料的股票"
    )
    periods: List[int] = Field(
        default=[5, 10, 20, 60, 120, 240],
        description="均線週期列表"
    )
    force_recalculate: bool = Field(
        default=False,
        description="是否強制重新計算"
    )
    batch_size: int = Field(
        default=50,
        description="批次處理大小",
        ge=1, le=500
    )


@router.get(
    "/statistics",
    summary="獲取均線統計資訊",
    description="獲取系統中均線計算的統計資訊，包括已計算股票數量、總記錄數、最新計算日期等",
    response_description="均線統計資訊"
)
async def get_moving_averages_statistics(
    db: Session = Depends(get_db)
):
    """
    獲取均線統計資訊
    
    返回內容：
    - stocks_with_ma: 已計算均線的股票數量
    - total_ma_records: 總均線記錄數量
    - latest_calculation_date: 最新計算日期
    - calculation_completeness: 計算完整度百分比
    - total_stocks: 系統中總股票數量
    """
    try:
        service = MovingAveragesService(db)
        stats = service.get_statistics()
        
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"獲取均線統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取統計資訊失敗: {str(e)}")


@router.post(
    "/calculate",
    summary="計算均線（同步）",
    description="同步計算指定股票的移動平均線，適用於小量股票的即時計算",
    response_description="計算結果統計"
)
async def calculate_moving_averages(
    request: MovingAveragesCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    同步計算移動平均線
    
    參數：
    - stock_codes: 要計算的股票代碼列表（可選）
    - periods: 均線週期列表，預設為 [5, 10, 20, 60, 120, 240]
    - force_recalculate: 是否強制重新計算
    
    返回：
    - processed_stocks: 成功處理的股票數量
    - total_calculations: 總計算筆數
    - success_rate: 成功率百分比
    """
    try:
        service = MovingAveragesService(db)
        
        # 驗證均線週期
        if any(period <= 0 for period in request.periods):
            raise HTTPException(status_code=422, detail="均線週期必須為正數")
        
        # 驗證股票代號格式
        if request.stock_codes:
            for stock_code in request.stock_codes:
                if not service._validate_stock_code(stock_code):
                    raise HTTPException(
                        status_code=422, 
                        detail=f"無效的股票代號: {stock_code}. 必須為4位數且不以0開頭"
                    )
        
        result = service.calculate_moving_averages(
            stock_codes=request.stock_codes,
            periods=request.periods,
            force_recalculate=request.force_recalculate
        )
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算均線失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"計算均線失敗: {str(e)}")


@router.get(
    "/query/{stock_code}",
    summary="查詢股票均線資料",
    description="查詢特定股票的移動平均線歷史資料，支援日期範圍篩選和分頁",
    response_description="股票均線歷史資料"
)
async def query_moving_averages(
    stock_code: str = Path(
        ...,
        description="股票代號",
        example="2330",
        regex=r"^\d{4}$"
    ),
    start_date: Optional[str] = Query(
        None,
        description="開始日期 (YYYY-MM-DD)",
        example="2025-01-01"
    ),
    end_date: Optional[str] = Query(
        None,
        description="結束日期 (YYYY-MM-DD)",
        example="2025-09-12"
    ),
    periods: Optional[str] = Query(
        None,
        description="查詢的均線週期，逗號分隔",
        example="5,10,20,60"
    ),
    page: int = Query(
        1,
        description="頁碼",
        ge=1
    ),
    limit: int = Query(
        100,
        description="每頁記錄數",
        ge=1, le=1000
    ),
    db: Session = Depends(get_db)
):
    """
    查詢股票移動平均線資料
    
    支援的查詢參數：
    - start_date/end_date: 日期範圍篩選
    - periods: 指定查詢的均線週期
    - page/limit: 分頁參數
    
    返回資料包含：
    - 交易日期、收盤價
    - MA5, MA10, MA20, MA60, MA120, MA240
    """
    try:
        service = MovingAveragesService(db)
        
        # 解析週期參數
        periods_list = None
        if periods:
            try:
                periods_list = [int(p.strip()) for p in periods.split(',')]
            except ValueError:
                raise HTTPException(status_code=422, detail="無效的週期格式，請使用逗號分隔的數字")
        
        result = service.query_moving_averages(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            periods=periods_list,
            page=page,
            limit=limit
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "查詢失敗"))
        
        return {
            "status": "success",
            "stock_code": stock_code,
            "data": result["data"],
            "pagination": {
                "page": result["page"],
                "limit": result["limit"],
                "total_records": result["total_records"],
                "total_pages": result["total_pages"]
            },
            "query_params": {
                "start_date": start_date,
                "end_date": end_date,
                "periods": periods_list
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢均線資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@router.post(
    "/calculate-async",
    summary="計算均線（非同步）",
    description="啟動非同步任務來計算移動平均線，適用於大量股票的批次計算",
    response_description="非同步任務資訊"
)
async def start_async_calculation(
    request: MovingAveragesAsyncRequest,
    db: Session = Depends(get_db)
):
    """
    啟動非同步均線計算任務
    
    適用於大量股票的批次計算，會在背景執行：
    - 支援批次處理以降低記憶體使用
    - 提供任務進度追蹤
    - 支援任務取消功能
    
    返回任務ID供後續查詢狀態使用
    """
    try:
        service = MovingAveragesService(db)
        
        # 驗證參數
        if any(period <= 0 for period in request.periods):
            raise HTTPException(status_code=422, detail="均線週期必須為正數")
        
        result = service.start_async_calculation(
            stock_codes=request.stock_codes,
            periods=request.periods,
            force_recalculate=request.force_recalculate,
            batch_size=request.batch_size
        )
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"啟動非同步計算失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動非同步計算失敗: {str(e)}")


@router.get(
    "/task-status/{task_id}",
    summary="查詢非同步任務狀態",
    description="查詢非同步均線計算任務的執行狀態和進度",
    response_description="任務狀態資訊"
)
async def get_task_status(
    task_id: str = Path(
        ...,
        description="任務ID",
        example="12345678-1234-1234-1234-123456789012"
    ),
    db: Session = Depends(get_db)
):
    """
    查詢非同步任務執行狀態
    
    返回內容：
    - state: 任務狀態 (PENDING, PROGRESS, SUCCESS, FAILURE)
    - current/total: 當前進度
    - percentage: 完成百分比
    - stage: 當前執行階段
    - result: 執行結果（完成後）
    - error: 錯誤訊息（失敗後）
    """
    try:
        service = MovingAveragesService(db)
        result = service.get_task_status(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "查詢失敗"))
        
        return {
            "status": "success",
            "task_id": task_id,
            "data": result["data"],
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢任務狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢任務狀態失敗: {str(e)}")


@router.delete(
    "/task/{task_id}",
    summary="取消非同步任務",
    description="取消正在執行的非同步均線計算任務",
    response_description="取消操作結果"
)
async def cancel_task(
    task_id: str = Path(
        ...,
        description="任務ID",
        example="12345678-1234-1234-1234-123456789012"
    ),
    db: Session = Depends(get_db)
):
    """
    取消非同步任務
    
    注意：
    - 只能取消正在執行或等待中的任務
    - 已完成的任務無法取消
    - 取消後的任務狀態會變為 REVOKED
    """
    try:
        service = MovingAveragesService(db)
        result = service.cancel_task(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "取消失敗"))
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": result["message"],
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")


@router.get(
    "/validate",
    summary="驗證均線資料一致性",
    description="檢查均線資料的完整性和一致性，並修復發現的問題",
    response_description="驗證結果統計"
)
async def validate_moving_averages(
    stock_code: Optional[str] = Query(
        None,
        description="指定股票代號，為空則驗證所有股票",
        regex=r"^\d{4}$"
    ),
    db: Session = Depends(get_db)
):
    """
    驗證均線資料一致性
    
    檢查項目：
    - 均線值與歷史股價的一致性
    - 缺失的均線資料
    - 異常的均線數值
    
    自動修復功能：
    - 重新計算異常的均線值
    - 補充缺失的資料
    """
    try:
        service = MovingAveragesService(db)
        result = service.validate_data_consistency(stock_code)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "驗證失敗"))
        
        return {
            "status": "success",
            "data": result,
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"驗證均線資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")


@router.post(
    "/clear",
    summary="清除均線資料",
    description="清除指定股票或所有股票的均線資料，此操作無法復原",
    response_description="清除操作結果"
)
async def clear_moving_averages(
    stock_code: Optional[str] = Body(
        None,
        description="指定股票代號，為空則清除所有均線資料",
        example="2330"
    ),
    db: Session = Depends(get_db)
):
    """
    清除均線資料
    
    警告：此操作無法復原！
    
    用法：
    - 指定 stock_code: 清除特定股票的均線資料
    - 不指定 stock_code: 清除所有均線資料
    
    建議在清除前先備份重要資料
    """
    try:
        service = MovingAveragesService(db)
        
        # 驗證股票代號（如果提供）
        if stock_code and not service._validate_stock_code(stock_code):
            raise HTTPException(
                status_code=422, 
                detail=f"無效的股票代號: {stock_code}. 必須為4位數且不以0開頭"
            )
        
        result = service.clear_moving_averages(stock_code)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "清除失敗"))
        
        return {
            "status": "success",
            "data": result,
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除均線資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除失敗: {str(e)}")