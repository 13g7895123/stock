"""交易日檢查API端點 - Trading Days Analysis API Endpoints."""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.trading_days_service import TradingDaysService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/missing-summary", response_model=Dict[str, Any])
async def get_missing_trading_days_summary(
    days_back: int = Query(30, description="檢查過去幾天的資料，預設30天", ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取缺少的交易日統計摘要。

    - **days_back**: 檢查過去幾天的資料，預設30天（1-365天）

    Returns:
        Dict containing missing trading days summary including:
        - 分析期間統計
        - 缺少的交易日列表
        - 資料完整性評分
        - 可能的原因分析

    Examples:
        - 檢查過去30天: /trading-days/missing-summary
        - 檢查過去7天: /trading-days/missing-summary?days_back=7
        - 檢查過去90天: /trading-days/missing-summary?days_back=90
    """
    try:
        logger.info(f"開始檢查過去 {days_back} 天的缺少交易日")

        # 初始化交易日檢查服務
        trading_days_service = TradingDaysService(db_session=db)

        # 獲取缺少交易日摘要
        result = trading_days_service.get_missing_trading_days_summary(days_back)

        if result["status"] != "success":
            logger.error(f"獲取缺少交易日摘要失敗: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"無法獲取缺少交易日摘要: {result.get('error', '未知錯誤')}"
            )

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功分析過去 {days_back} 天的交易日資料",
            "data": result["summary"],
            "metadata": {
                "analysis_type": "missing_trading_days",
                "service_version": "1.0.0",
                "timestamp": result.get("timestamp")
            }
        }

        logger.info(f"成功回傳缺少交易日摘要，分析期間: {days_back} 天")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理缺少交易日摘要請求時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/stock-completeness", response_model=Dict[str, Any])
async def get_stock_missing_data_summary(
    stock_code: Optional[str] = Query(None, description="股票代號（4位數字），留空則分析所有股票"),
    days_back: int = Query(30, description="檢查過去幾天的資料，預設30天", ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取股票資料完整性分析。

    - **stock_code**: 股票代號（4位數字），留空則分析所有股票
    - **days_back**: 檢查過去幾天的資料，預設30天（1-365天）

    Returns:
        Dict containing stock data completeness analysis including:
        - 特定股票或所有股票的資料完整性統計
        - 缺少資料的詳細分析
        - 資料完整率排名

    Examples:
        - 分析台積電資料完整性: /trading-days/stock-completeness?stock_code=2330
        - 分析所有股票完整性: /trading-days/stock-completeness
        - 分析過去7天資料: /trading-days/stock-completeness?days_back=7
    """
    try:
        # 驗證股票代號格式（如果提供）
        if stock_code:
            if not stock_code or len(stock_code) != 4 or not stock_code.isdigit() or stock_code.startswith("0"):
                raise HTTPException(
                    status_code=400,
                    detail=f"無效的股票代號: {stock_code}. 必須是4位數字且不能以0開頭"
                )

        target_desc = f"股票 {stock_code}" if stock_code else "所有股票"
        logger.info(f"開始分析 {target_desc} 過去 {days_back} 天的資料完整性")

        # 初始化交易日檢查服務
        trading_days_service = TradingDaysService(db_session=db)

        # 獲取股票資料完整性分析
        result = trading_days_service.get_stock_missing_data_summary(stock_code, days_back)

        if result["status"] != "success":
            logger.error(f"獲取股票資料完整性分析失敗: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"無法獲取股票資料完整性分析: {result.get('error', '未知錯誤')}"
            )

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功分析 {target_desc} 過去 {days_back} 天的資料完整性",
            "data": result.get("analysis") or result,
            "metadata": {
                "analysis_type": "stock_completeness",
                "target": stock_code or "all_stocks",
                "days_analyzed": days_back,
                "service_version": "1.0.0",
                "timestamp": result.get("timestamp")
            }
        }

        logger.info(f"成功回傳 {target_desc} 的資料完整性分析")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理股票資料完整性分析請求時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.post("/fix-suggestions", response_model=Dict[str, Any])
async def get_missing_data_fix_suggestions(
    missing_dates: List[str],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取缺少資料的修復建議。

    - **missing_dates**: 缺少的日期列表，格式為 YYYY-MM-DD

    Returns:
        Dict containing suggestions for fixing missing data including:
        - 每個缺少日期的修復建議
        - 建議的API端點
        - 操作優先級

    Request Body Example:
        ```json
        ["2024-09-20", "2024-09-19", "2024-09-18"]
        ```
    """
    try:
        if not missing_dates:
            raise HTTPException(
                status_code=400,
                detail="缺少日期列表不能為空"
            )

        logger.info(f"開始為 {len(missing_dates)} 個缺少的日期生成修復建議")

        # 初始化交易日檢查服務
        trading_days_service = TradingDaysService(db_session=db)

        # 獲取修復建議
        result = await trading_days_service.suggest_missing_data_fixes(missing_dates)

        if result["status"] != "success":
            logger.error(f"生成修復建議失敗: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"無法生成修復建議: {result.get('error', '未知錯誤')}"
            )

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功為 {len(missing_dates)} 個缺少日期生成修復建議",
            "data": result,
            "metadata": {
                "analysis_type": "fix_suggestions",
                "dates_analyzed": len(missing_dates),
                "service_version": "1.0.0"
            }
        }

        logger.info(f"成功生成 {len(result.get('suggestions', []))} 個修復建議")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理修復建議請求時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/info", response_model=Dict[str, Any])
async def get_trading_days_service_info() -> Dict[str, Any]:
    """
    獲取交易日檢查服務資訊。

    Returns:
        Dict containing trading days analysis service information
    """
    return {
        "service_name": "交易日檢查分析服務",
        "description": "分析和檢查股票交易資料的完整性，識別缺少的交易日",
        "features": [
            "缺少交易日統計摘要",
            "股票資料完整性分析",
            "修復建議生成",
            "多時間範圍分析支援",
            "個別股票深度分析"
        ],
        "endpoints": {
            "missing_summary": "/api/v1/trading-days/missing-summary",
            "stock_completeness": "/api/v1/trading-days/stock-completeness",
            "fix_suggestions": "/api/v1/trading-days/fix-suggestions",
            "service_info": "/api/v1/trading-days/info"
        },
        "analysis_capabilities": {
            "max_days_back": 365,
            "min_days_back": 1,
            "default_analysis_period": 30,
            "supported_date_format": "YYYY-MM-DD",
            "weekend_handling": "自動排除週末"
        },
        "version": "1.0.0",
        "timestamp": "2024-09-22T00:00:00Z"
    }


@router.get("/smart-analysis", response_model=Dict[str, Any])
async def get_smart_missing_trading_days_analysis(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    智能分析缺少的交易日，自動調整檢查範圍。

    Returns:
        Dict containing smart missing trading days analysis including:
        - 根據最新資料自動選擇的分析期間
        - 缺少的交易日詳細分析
        - 智能分析原因說明

    Examples:
        - 智能檢查缺少的交易日: /trading-days/smart-analysis
    """
    try:
        logger.info("開始執行智能缺少交易日分析")

        # 初始化交易日檢查服務
        trading_days_service = TradingDaysService(db_session=db)

        # 執行智能分析
        result = trading_days_service.get_smart_missing_trading_days_analysis()

        if result["status"] != "success":
            logger.error(f"智能分析失敗: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"智能分析失敗: {result.get('error', '未知錯誤')}"
            )

        # 準備回應
        response = {
            "status": "success",
            "message": "智能分析缺少交易日完成",
            "data": result["summary"],
            "metadata": {
                "analysis_type": "smart_missing_trading_days",
                "service_version": "1.0.0",
                "timestamp": result.get("timestamp")
            }
        }

        logger.info("成功完成智能缺少交易日分析")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理智能分析請求時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/smart-batch-update-analysis", response_model=Dict[str, Any])
async def get_smart_batch_update_analysis(
    days_back: int = Query(30, description="檢查過去幾天的資料，預設30天", ge=1, le=90),
    force_refresh: bool = Query(False, description="強制檢查所有股票是否需要刷新，即使沒有缺少資料"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    智能批次更新分析 - 分析股票資料完整性並生成證交所API修復清單。

    此端點專為Point 13設計，會：
    1. 檢查所有股票的資料完整性
    2. 識別缺少的交易日
    3. 分析哪些股票/日期可以透過證交所API修復
    4. 生成可執行的批次更新清單

    - **days_back**: 檢查過去幾天的資料，預設30天（1-90天）

    Returns:
        Dict containing batch update analysis with actionable fix list
    """
    try:
        logger.info(f"開始執行智能批次更新分析，檢查過去 {days_back} 天")

        # 初始化交易日檢查服務
        trading_days_service = TradingDaysService(db_session=db)

        # 1. 獲取缺少交易日摘要
        missing_summary = trading_days_service.get_missing_trading_days_summary(days_back)

        if missing_summary["status"] != "success":
            logger.error(f"獲取缺少交易日摘要失敗: {missing_summary.get('error')}")
            raise HTTPException(
                status_code=503,
                detail=f"無法分析交易日資料: {missing_summary.get('error', '未知錯誤')}"
            )

        # 解析回應結構
        if "data" in missing_summary:
            missing_data = missing_summary["data"]
        else:
            missing_data = missing_summary
        missing_dates = missing_data.get("missing_dates", [])
        statistics = missing_data.get("statistics", {})

        # 2. 分析可以透過證交所API修復的日期
        fixable_dates = []
        skipped_dates = []

        # 如果啟用強制刷新模式且沒有缺少的日期，生成最近交易日的刷新清單
        if force_refresh and len(missing_dates) == 0:
            logger.info("啟用強制刷新模式，生成近期交易日刷新清單")
            from datetime import datetime, timedelta

            # 生成過去5個交易日的刷新清單（排除週末）
            current_date = datetime.now()
            refresh_count = 0
            check_days = 0

            while refresh_count < 5 and check_days < 14:  # 最多檢查14天找到5個工作日
                target_date = current_date - timedelta(days=check_days + 1)
                # 排除週末（週六=5, 週日=6）
                if target_date.weekday() < 5:  # 週一到週五
                    date_str = target_date.strftime('%Y-%m-%d')
                    fixable_dates.append({
                        "date": date_str,
                        "weekday": target_date.strftime('%A'),
                        "days_ago": check_days + 1,
                        "reasons": ["強制刷新模式", "確保資料最新"]
                    })
                    refresh_count += 1
                check_days += 1

            logger.info(f"強制刷新模式：生成 {len(fixable_dates)} 個交易日進行資料刷新")

        else:
            # 原有的缺少日期分析邏輯
            for missing_date in missing_dates:
                date_info = {
                    "date": missing_date["date"],
                    "weekday": missing_date["weekday"],
                    "days_ago": missing_date["days_ago"],
                    "reasons": missing_date.get("possible_reasons", [])
                }

                # 只選擇非週末且非最近的日期（可以安全使用證交所API修復）
                if not missing_date.get("is_weekend", False) and not missing_date.get("is_recent", False):
                    fixable_dates.append(date_info)
                else:
                    skipped_info = date_info.copy()
                    skipped_info["skip_reason"] = []
                    if missing_date.get("is_weekend", False):
                        skipped_info["skip_reason"].append("週末非交易日")
                    if missing_date.get("is_recent", False):
                        skipped_info["skip_reason"].append("日期太接近現在")
                    skipped_dates.append(skipped_info)

        # 3. 生成批次更新執行計劃
        execution_plan = {
            "total_missing_dates": len(missing_dates),
            "fixable_dates_count": len(fixable_dates),
            "skipped_dates_count": len(skipped_dates),
            "estimated_api_calls": len(fixable_dates),
            "estimated_time_minutes": len(fixable_dates) * 0.5,  # 估計每個API調用30秒
            "success_probability": "高" if len(fixable_dates) <= 10 else "中" if len(fixable_dates) <= 30 else "需要分批處理"
        }

        # 4. 生成API調用清單
        api_calls = []
        for date_info in fixable_dates:
            api_calls.append({
                "api_endpoint": f"/api/v1/twse/historical-all/{date_info['date'].replace('-', '')}?save_to_db=true",
                "date": date_info["date"],
                "method": "GET",
                "description": f"獲取 {date_info['date']} ({date_info['weekday']}) 的證交所資料並存入資料庫"
            })

        # 5. 建議的執行順序（由舊到新）
        api_calls.sort(key=lambda x: x["date"])

        # 準備回應
        response = {
            "status": "success",
            "message": f"智能批次更新分析完成，發現 {len(fixable_dates)} 個可修復的交易日",
            "analysis": {
                "period": missing_data.get("analysis_period", {}),
                "overall_statistics": statistics,
                "completeness_rate": statistics.get("completeness_rate", 100),
                "data_quality": "優秀" if statistics.get("completeness_rate", 100) >= 95 else
                               "良好" if statistics.get("completeness_rate", 100) >= 90 else "需要改善"
            },
            "execution_plan": execution_plan,
            "fixable_dates": fixable_dates,
            "skipped_dates": skipped_dates,
            "api_calls": api_calls,
            "recommendations": {
                "immediate_action": len(fixable_dates) > 0,
                "action_description": f"建議立即執行 {len(fixable_dates)} 個證交所API調用來修復缺少的資料" if len(fixable_dates) > 0 else "目前沒有需要修復的資料",
                "batch_size": min(len(fixable_dates), 10) if len(fixable_dates) > 0 else 0,
                "execution_mode": "順序執行" if len(fixable_dates) <= 10 else "分批執行"
            },
            "metadata": {
                "analysis_type": "smart_batch_update_analysis",
                "service_version": "1.0.0",
                "timestamp": missing_summary.get("timestamp"),
                "can_auto_execute": len(fixable_dates) > 0
            }
        }

        logger.info(f"智能批次更新分析完成: {len(fixable_dates)} 個可修復日期, {len(api_calls)} 個API調用")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理智能批次更新分析請求時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"智能批次更新分析服務錯誤: {str(e)}"
        )