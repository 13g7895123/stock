"""API endpoints for institutional trading data (投信外資買賣超)."""

import logging
from datetime import datetime, date
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.institutional_trading_service import InstitutionalTradingService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["institutional-trading"],
    responses={404: {"description": "Not found"}},
)


@router.get("/statistics", response_model=Dict)
async def get_institutional_statistics(
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得投信外資買賣超統計資料。

    Returns:
        Dictionary containing institutional trading statistics including:
        - total_records: 總記錄數
        - total_stocks: 有資料的股票數
        - total_days: 有資料的天數
        - earliest_date: 最早日期
        - latest_date: 最新日期
        - latest_summary: 最新一日統計摘要
    """
    try:
        service = InstitutionalTradingService(db)
        stats = service.get_institutional_statistics()

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting institutional statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/latest", response_model=Dict)
async def update_latest_institutional_data(
    db: Session = Depends(get_db)
) -> Dict:
    """
    更新最新交易日的投信外資買賣超資料。

    智能地尋找最近有資料的交易日並進行更新。

    Returns:
        Dictionary with update results
    """
    try:
        from datetime import timedelta

        service = InstitutionalTradingService(db)

        # 嘗試最近7天的交易日，直到找到有資料的日期
        for days_back in range(7):
            target_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

            logger.info(f"Trying to update institutional data for date: {target_date}")
            result = await service.update_institutional_data_for_date(target_date)

            # 如果成功找到並處理了資料，立即返回
            if (result.get("status") == "success" and
                not result.get("no_data") and
                result.get("total_processed", 0) > 0):

                logger.info(f"Successfully found and updated data for {target_date}")
                return {
                    "status": "success",
                    "message": f"Successfully updated latest institutional data for {target_date}",
                    "data": result,
                    "found_date": target_date
                }

            # 如果是沒有資料的情況，繼續嘗試前一天
            if result.get("no_data"):
                logger.info(f"No data available for {target_date}, trying previous day")
                continue

            # 如果是其他錯誤，也記錄並繼續
            if result.get("status") == "error":
                logger.warning(f"Error for {target_date}: {result.get('message')}")
                continue

        # 如果7天內都沒有找到可用的資料
        raise HTTPException(
            status_code=404,
            detail="No institutional trading data available in the past 7 days"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating latest institutional data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/batch", response_model=Dict)
async def batch_update_institutional_data(
    days_back: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict:
    """
    批次更新近期投信外資買賣超資料。

    Args:
        days_back: 回溯天數 (1-365天，預設30天)

    Returns:
        Dictionary with batch update results
    """
    try:
        service = InstitutionalTradingService(db)
        result = await service.batch_update_institutional_data(days_back)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return {
            "status": "success",
            "message": f"Successfully completed batch update for {days_back} days",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch update institutional data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/{date}", response_model=Dict)
async def update_institutional_data(
    date: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    更新指定日期的投信外資買賣超資料。

    Args:
        date: 交易日期，格式 YYYYMMDD (e.g., "20240920")

    Returns:
        Dictionary with update results:
        - total_processed: 處理的記錄數
        - created_count: 新增的記錄數
        - updated_count: 更新的記錄數
        - error_count: 錯誤的記錄數
    """
    try:
        # 驗證日期格式
        try:
            datetime.strptime(date, "%Y%m%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYYMMDD (e.g., 20240920)"
            )

        service = InstitutionalTradingService(db)
        result = await service.update_institutional_data_for_date(date)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return {
            "status": "success",
            "message": f"Successfully updated institutional data for {date}",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating institutional data for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}", response_model=Dict)
async def get_stock_institutional_data(
    stock_code: str,
    limit: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得特定股票的投信外資買賣超資料。

    Args:
        stock_code: 股票代號 (e.g., "2330")
        limit: 限制筆數 (1-365，預設30)

    Returns:
        Dictionary containing:
        - stock_code: 股票代號
        - data: 投信外資買賣超資料列表
        - total_records: 總筆數
    """
    try:
        # 驗證股票代號格式
        if not stock_code or not stock_code.isdigit() or len(stock_code) < 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock code format"
            )

        service = InstitutionalTradingService(db)
        data = service.get_stock_institutional_data(stock_code, limit)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No institutional data found for stock {stock_code}"
            )

        return {
            "status": "success",
            "stock_code": stock_code,
            "data": data,
            "total_records": len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institutional data for stock {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/completeness", response_model=Dict)
async def check_institutional_data_completeness(
    days_back: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict:
    """
    檢查投信外資買賣超資料的完整性。

    Args:
        days_back: 檢查過去天數 (1-365天，預設30天)

    Returns:
        Dictionary containing completeness analysis:
        - analysis_period: 分析期間
        - total_stocks_in_system: 系統中總股票數
        - stocks_with_data: 有資料的股票數
        - stocks_without_data: 缺少資料的股票數
        - completeness_rate: 完整率百分比
        - latest_date: 最新資料日期
    """
    try:
        from datetime import datetime, timedelta
        from src.models.stock import Stock

        # 計算分析期間
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        # 查詢系統中的股票總數
        total_stocks_query = db.query(Stock).filter(Stock.is_active == True)
        total_stocks = total_stocks_query.count()

        # 查詢有投信外資資料的股票數
        from src.models.stock import InstitutionalTradingData
        stocks_with_data_query = db.query(InstitutionalTradingData.stock_code).filter(
            InstitutionalTradingData.trade_date >= start_date,
            InstitutionalTradingData.trade_date <= end_date
        ).distinct()
        stocks_with_data = stocks_with_data_query.count()

        # 計算完整率
        completeness_rate = (stocks_with_data / total_stocks * 100) if total_stocks > 0 else 0

        # 最新資料日期
        from sqlalchemy import func
        latest_date = db.query(func.max(InstitutionalTradingData.trade_date)).scalar()

        # 缺少資料的股票列表 (前10個)
        stocks_with_data_codes = [row[0] for row in stocks_with_data_query.all()]
        stocks_without_data = db.query(Stock.stock_code, Stock.stock_name).filter(
            Stock.is_active == True,
            ~Stock.stock_code.in_(stocks_with_data_codes)
        ).limit(10).all()

        return {
            "status": "success",
            "data": {
                "analysis_period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days_back
                },
                "total_stocks_in_system": total_stocks,
                "stocks_with_data": stocks_with_data,
                "stocks_without_data": total_stocks - stocks_with_data,
                "completeness_rate": round(completeness_rate, 2),
                "latest_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
                "sample_stocks_without_data": [
                    {"stock_code": s.stock_code, "stock_name": s.stock_name}
                    for s in stocks_without_data
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error checking institutional data completeness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{date}", response_model=Dict)
async def get_daily_institutional_summary(
    date: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得指定日期的投信外資買賣超總覽。

    Args:
        date: 交易日期，格式 YYYYMMDD

    Returns:
        Dictionary containing daily summary of institutional trading
    """
    try:
        # 驗證日期格式
        try:
            trade_date = datetime.strptime(date, "%Y%m%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYYMMDD (e.g., 20240920)"
            )

        from src.models.stock import InstitutionalTradingData
        from sqlalchemy import func

        # 查詢該日期的總覽資料
        summary = db.query(
            func.sum(InstitutionalTradingData.foreign_net).label('foreign_total'),
            func.sum(InstitutionalTradingData.investment_trust_net).label('trust_total'),
            func.sum(InstitutionalTradingData.dealer_net).label('dealer_total'),
            func.sum(InstitutionalTradingData.total_institutional_net).label('total_net'),
            func.count(InstitutionalTradingData.id).label('stock_count')
        ).filter(
            InstitutionalTradingData.trade_date == trade_date
        ).first()

        if not summary or summary.stock_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No institutional trading data found for {date}"
            )

        return {
            "status": "success",
            "date": date,
            "data": {
                "foreign_net_total": int(summary.foreign_total or 0),
                "investment_trust_net_total": int(summary.trust_total or 0),
                "dealer_net_total": int(summary.dealer_total or 0),
                "total_institutional_net": int(summary.total_net or 0),
                "stock_count": summary.stock_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily institutional summary for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/latest", response_model=Dict)
async def get_latest_institutional_rankings(
    category: str = Query(default="total", regex="^(foreign|investment_trust|dealer|total)$"),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="amount", regex="^(amount|capital_ratio)$"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得最新交易日的投信外資買賣超排名。

    Args:
        category: 排名類別 - 'foreign', 'investment_trust', 'dealer', 'total'
        limit: 限制筆數 (1-100，預設20)
        sort_by: 排序方式 - 'amount'（按金額）, 'capital_ratio'（按股本比）

    Returns:
        Dictionary containing:
        - buy_rankings: 買超排名
        - sell_rankings: 賣超排名
        - latest_date: 最新交易日期
        - category: 排名類別
        - sort_by: 排序方式
    """
    try:
        from src.models.stock import InstitutionalTradingData
        from sqlalchemy import func, desc, asc

        # 取得最新交易日期
        latest_date = db.query(func.max(InstitutionalTradingData.trade_date)).scalar()

        if not latest_date:
            raise HTTPException(
                status_code=404,
                detail="No institutional trading data found"
            )

        # 根據類別選擇對應的欄位
        category_field_map = {
            "foreign": InstitutionalTradingData.foreign_net,
            "investment_trust": InstitutionalTradingData.investment_trust_net,
            "dealer": InstitutionalTradingData.dealer_net,
            "total": InstitutionalTradingData.total_institutional_net
        }

        net_field = category_field_map[category]

        # 基本查詢 - 最新交易日的資料，包含股本資訊
        from src.models.stock import Stock

        base_query = db.query(
            InstitutionalTradingData.stock_code,
            InstitutionalTradingData.stock_name,
            InstitutionalTradingData.foreign_net,
            InstitutionalTradingData.investment_trust_net,
            InstitutionalTradingData.dealer_net,
            InstitutionalTradingData.total_institutional_net,
            net_field.label('net_amount'),
            Stock.capital_stock
        ).join(
            Stock, InstitutionalTradingData.stock_code == Stock.stock_code, isouter=True
        ).filter(
            InstitutionalTradingData.trade_date == latest_date,
            net_field != 0  # 排除淨額為0的記錄
        )

        # 根據排序方式決定排序邏輯
        if sort_by == "capital_ratio":
            # 按股本比排序 - 需要先計算股本比，然後過濾出有股本資料的記錄
            from sqlalchemy import case

            # 計算股本比作為額外欄位
            capital_ratio_expr = case(
                (Stock.capital_stock.is_(None), None),
                (Stock.capital_stock == 0, None),
                else_=(net_field / (Stock.capital_stock / 10)) * 100
            ).label('capital_ratio')

            query_with_ratio = db.query(
                InstitutionalTradingData.stock_code,
                InstitutionalTradingData.stock_name,
                InstitutionalTradingData.foreign_net,
                InstitutionalTradingData.investment_trust_net,
                InstitutionalTradingData.dealer_net,
                InstitutionalTradingData.total_institutional_net,
                net_field.label('net_amount'),
                Stock.capital_stock,
                capital_ratio_expr
            ).join(
                Stock, InstitutionalTradingData.stock_code == Stock.stock_code, isouter=True
            ).filter(
                InstitutionalTradingData.trade_date == latest_date,
                net_field != 0,
                Stock.capital_stock.is_not(None),  # 只取有股本資料的記錄
                Stock.capital_stock > 0
            )

            # 買超排名 (正數，按股本比從大到小)
            buy_rankings = query_with_ratio.filter(
                net_field > 0
            ).order_by(desc(capital_ratio_expr)).limit(limit).all()

            # 賣超排名 (負數，按股本比絕對值從大到小)
            sell_rankings = query_with_ratio.filter(
                net_field < 0
            ).order_by(asc(capital_ratio_expr)).limit(limit).all()
        else:
            # 按金額排序 (原有邏輯)
            # 買超排名 (正數，從大到小)
            buy_rankings = base_query.filter(
                net_field > 0
            ).order_by(desc(net_field)).limit(limit).all()

            # 賣超排名 (負數，從小到大，即絕對值從大到小)
            sell_rankings = base_query.filter(
                net_field < 0
            ).order_by(asc(net_field)).limit(limit).all()

        # 格式化結果
        def format_ranking(records):
            result = []
            for idx, record in enumerate(records):
                # 計算股本比 (買賣超金額/股本*100%)
                capital_ratio = None
                if record.capital_stock and record.capital_stock > 0:
                    # 股本單位是元，買賣超單位是股數，需要轉換
                    # 假設每股面額為10元（台股標準）
                    capital_in_shares = record.capital_stock / 10
                    capital_ratio = (record.net_amount / capital_in_shares) * 100 if capital_in_shares > 0 else None

                result.append({
                    "rank": idx + 1,
                    "stock_code": record.stock_code,
                    "stock_name": record.stock_name,
                    "net_amount": record.net_amount,
                    "foreign_net": record.foreign_net,
                    "investment_trust_net": record.investment_trust_net,
                    "dealer_net": record.dealer_net,
                    "total_institutional_net": record.total_institutional_net,
                    "capital_stock": record.capital_stock,
                    "capital_ratio": round(capital_ratio, 4) if capital_ratio is not None else None
                })
            return result

        # 類別中文名稱映射
        category_names = {
            "foreign": "外資",
            "investment_trust": "投信",
            "dealer": "自營商",
            "total": "三大法人合計"
        }

        # 排序方式中文名稱映射
        sort_names = {
            "amount": "按金額排序",
            "capital_ratio": "按股本比排序"
        }

        return {
            "status": "success",
            "data": {
                "latest_date": latest_date.strftime("%Y-%m-%d"),
                "category": category,
                "category_name": category_names[category],
                "sort_by": sort_by,
                "sort_name": sort_names[sort_by],
                "buy_rankings": format_ranking(buy_rankings),
                "sell_rankings": format_ranking(sell_rankings),
                "buy_count": len(buy_rankings),
                "sell_count": len(sell_rankings)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institutional rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capital-ratio/rankings", response_model=Dict)
async def get_capital_ratio_rankings(
    days_back: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得指定期間的股本比累積排名。

    Args:
        days_back: 回溯天數 (1-365天，預設30天)
        limit: 限制筆數 (1-100，預設50)

    Returns:
        Dictionary containing:
        - period: 分析期間
        - buy_rankings: 買超股本比排名
        - sell_rankings: 賣超股本比排名
    """
    try:
        service = InstitutionalTradingService(db)
        result = service.get_capital_ratio_rankings(days_back, limit)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return {
            "status": "success",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting capital ratio rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capital-ratio/trends", response_model=Dict)
async def get_capital_ratio_trends(
    days_back: int = Query(default=30, ge=1, le=365),
    top_stocks: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得每日股本比趨勢資料。

    Args:
        days_back: 回溯天數 (1-365天，預設30天)
        top_stocks: 顯示前N檔股票 (1-50，預設10)

    Returns:
        Dictionary containing:
        - period: 分析期間
        - dates: 日期列表
        - trends: 股票趨勢資料
    """
    try:
        service = InstitutionalTradingService(db)
        result = service.get_daily_capital_ratio_trends(days_back, top_stocks)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return {
            "status": "success",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting capital ratio trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/{date}", response_model=Dict)
async def get_institutional_rankings_by_date(
    date: str,
    category: str = Query(default="total", regex="^(foreign|investment_trust|dealer|total)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict:
    """
    取得指定日期的投信外資買賣超排名。

    Args:
        date: 交易日期，格式 YYYYMMDD
        category: 排名類別 - 'foreign', 'investment_trust', 'dealer', 'total'
        limit: 限制筆數 (1-100，預設20)

    Returns:
        Dictionary containing buy/sell rankings for the specified date
    """
    try:
        # 驗證日期格式
        try:
            trade_date = datetime.strptime(date, "%Y%m%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYYMMDD (e.g., 20240920)"
            )

        from src.models.stock import InstitutionalTradingData
        from sqlalchemy import func, desc, asc

        # 根據類別選擇對應的欄位
        category_field_map = {
            "foreign": InstitutionalTradingData.foreign_net,
            "investment_trust": InstitutionalTradingData.investment_trust_net,
            "dealer": InstitutionalTradingData.dealer_net,
            "total": InstitutionalTradingData.total_institutional_net
        }

        net_field = category_field_map[category]

        # 基本查詢 - 指定交易日的資料，包含股本資訊
        from src.models.stock import Stock

        base_query = db.query(
            InstitutionalTradingData.stock_code,
            InstitutionalTradingData.stock_name,
            InstitutionalTradingData.foreign_net,
            InstitutionalTradingData.investment_trust_net,
            InstitutionalTradingData.dealer_net,
            InstitutionalTradingData.total_institutional_net,
            net_field.label('net_amount'),
            Stock.capital_stock
        ).join(
            Stock, InstitutionalTradingData.stock_code == Stock.stock_code, isouter=True
        ).filter(
            InstitutionalTradingData.trade_date == trade_date,
            net_field != 0  # 排除淨額為0的記錄
        )

        # 檢查是否有資料
        total_count = base_query.count()
        if total_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No institutional trading data found for {date}"
            )

        # 買超排名 (正數，從大到小)
        buy_rankings = base_query.filter(
            net_field > 0
        ).order_by(desc(net_field)).limit(limit).all()

        # 賣超排名 (負數，從小到大，即絕對值從大到小)
        sell_rankings = base_query.filter(
            net_field < 0
        ).order_by(asc(net_field)).limit(limit).all()

        # 格式化結果
        def format_ranking(records):
            result = []
            for idx, record in enumerate(records):
                # 計算股本比 (買賣超金額/股本*100%)
                capital_ratio = None
                if record.capital_stock and record.capital_stock > 0:
                    # 股本單位是元，買賣超單位是股數，需要轉換
                    # 假設每股面額為10元（台股標準）
                    capital_in_shares = record.capital_stock / 10
                    capital_ratio = (record.net_amount / capital_in_shares) * 100 if capital_in_shares > 0 else None

                result.append({
                    "rank": idx + 1,
                    "stock_code": record.stock_code,
                    "stock_name": record.stock_name,
                    "net_amount": record.net_amount,
                    "foreign_net": record.foreign_net,
                    "investment_trust_net": record.investment_trust_net,
                    "dealer_net": record.dealer_net,
                    "total_institutional_net": record.total_institutional_net,
                    "capital_stock": record.capital_stock,
                    "capital_ratio": round(capital_ratio, 4) if capital_ratio is not None else None
                })
            return result

        # 類別中文名稱映射
        category_names = {
            "foreign": "外資",
            "investment_trust": "投信",
            "dealer": "自營商",
            "total": "三大法人合計"
        }

        return {
            "status": "success",
            "data": {
                "trade_date": date,
                "category": category,
                "category_name": category_names[category],
                "buy_rankings": format_ranking(buy_rankings),
                "sell_rankings": format_ranking(sell_rankings),
                "buy_count": len(buy_rankings),
                "sell_count": len(sell_rankings),
                "total_stocks": total_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institutional rankings for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))