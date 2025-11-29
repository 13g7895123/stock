"""股票選股結果 API 端點"""

import logging
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.stock_selection_service import StockSelectionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/results")
async def get_selection_results(
    selection_date: Optional[date] = Query(None, description="選股日期，預設為最新交易日"),
    strategies: Optional[str] = Query(None, description="策略類型，逗號分隔，如: perfect_bull,short_bull,bear"),
    db: Session = Depends(get_db)
):
    """取得選股結果

    Args:
        selection_date: 選股日期，預設為最新交易日
        strategies: 策略類型，可選值：perfect_bull（完美多頭）, short_bull（短線多頭）, bear（空頭）
        db: 資料庫會話

    Returns:
        選股結果，包含各策略選出的股票列表
    """
    try:
        service = StockSelectionService(db)

        # 解析策略類型
        strategy_types = None
        if strategies:
            strategy_types = [s.strip() for s in strategies.split(',')]

            # 驗證策略類型
            valid_strategies = ['perfect_bull', 'short_bull', 'bear', 'all_stocks']
            for strategy in strategy_types:
                if strategy not in valid_strategies:
                    raise HTTPException(
                        status_code=400,
                        detail=f"無效的策略類型: {strategy}。有效策略: {', '.join(valid_strategies)}"
                    )

        # 取得選股結果
        results = service.get_stock_selection_results(
            selection_date=selection_date,
            strategy_types=strategy_types
        )

        return {
            "status": "success",
            "data": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得選股結果失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取得選股結果失敗: {str(e)}"
        )


@router.get("/latest-date")
async def get_latest_trading_date(
    db: Session = Depends(get_db)
):
    """取得最新交易日期

    Returns:
        最新交易日期
    """
    try:
        service = StockSelectionService(db)
        latest_date = service.get_latest_trading_date()

        return {
            "status": "success",
            "data": {
                "latest_date": latest_date.strftime('%Y-%m-%d') if latest_date else None
            }
        }

    except Exception as e:
        logger.error(f"取得最新交易日期失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取得最新交易日期失敗: {str(e)}"
        )


@router.get("/stock/{stock_code}/ma-status")
async def get_stock_ma_status(
    stock_code: str,
    check_date: Optional[date] = Query(None, description="檢查日期，預設為最新交易日"),
    db: Session = Depends(get_db)
):
    """取得個股均線狀態

    Args:
        stock_code: 股票代號
        check_date: 檢查日期
        db: 資料庫會話

    Returns:
        個股的均線排列狀態
    """
    try:
        from src.models.stock import MovingAverages, StockDailyData, Stock
        from sqlalchemy import and_

        service = StockSelectionService(db)

        # 如果沒有指定日期，使用最新交易日
        if not check_date:
            check_date = service.get_latest_trading_date()

        # 查詢均線資料
        ma_data = db.query(
            MovingAverages,
            StockDailyData.close_price,
            StockDailyData.volume,
            StockDailyData.price_change,
            Stock.stock_name
        ).join(
            StockDailyData,
            and_(
                MovingAverages.stock_id == StockDailyData.stock_code,
                MovingAverages.trade_date == StockDailyData.trade_date
            )
        ).join(
            Stock,
            MovingAverages.stock_id == Stock.stock_code
        ).filter(
            MovingAverages.stock_id == stock_code,
            MovingAverages.trade_date == check_date
        ).first()

        if not ma_data:
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票 {stock_code} 在 {check_date} 的均線資料"
            )

        ma, close_price, volume, price_change, stock_name = ma_data

        # 判斷均線狀態
        ma_status = {
            'perfect_bull': False,
            'short_bull': False,
            'bear': False,
            'neutral': False
        }

        # 判斷完美多頭
        if (ma.ma_5 and ma.ma_10 and ma.ma_20 and ma.ma_60 and ma.ma_120 and ma.ma_240):
            if (ma.ma_5 > ma.ma_10 > ma.ma_20 > ma.ma_60 > ma.ma_120 > ma.ma_240 and
                close_price > ma.ma_5):
                ma_status['perfect_bull'] = True

        # 判斷短線多頭
        if (ma.ma_5 and ma.ma_10 and ma.ma_20):
            if (ma.ma_5 > ma.ma_10 > ma.ma_20 and close_price > ma.ma_5):
                if not ma_status['perfect_bull']:  # 排除已經是完美多頭的
                    ma_status['short_bull'] = True

        # 判斷空頭
        if (ma.ma_5 and ma.ma_10 and ma.ma_20 and ma.ma_60):
            if (ma.ma_5 < ma.ma_10 < ma.ma_20 < ma.ma_60 and close_price < ma.ma_5):
                ma_status['bear'] = True

        # 如果都不是，則為中性
        if not any([ma_status['perfect_bull'], ma_status['short_bull'], ma_status['bear']]):
            ma_status['neutral'] = True

        # 計算乖離率
        ma_bias = round((float(close_price) - float(ma.ma_5)) / float(ma.ma_5) * 100, 2) if ma.ma_5 else None

        return {
            "status": "success",
            "data": {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "check_date": check_date.strftime('%Y-%m-%d'),
                "close_price": float(close_price),
                "price_change": float(price_change) if price_change else 0,
                "volume": int(volume),
                "ma_data": {
                    "ma_5": float(ma.ma_5) if ma.ma_5 else None,
                    "ma_10": float(ma.ma_10) if ma.ma_10 else None,
                    "ma_20": float(ma.ma_20) if ma.ma_20 else None,
                    "ma_60": float(ma.ma_60) if ma.ma_60 else None,
                    "ma_120": float(ma.ma_120) if ma.ma_120 else None,
                    "ma_240": float(ma.ma_240) if ma.ma_240 else None
                },
                "ma_bias": ma_bias,
                "ma_status": ma_status
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得個股均線狀態失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取得個股均線狀態失敗: {str(e)}"
        )