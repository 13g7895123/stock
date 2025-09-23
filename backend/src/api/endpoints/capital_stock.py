"""API endpoints for stock capital data."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.capital_stock_service import CapitalStockService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["capital-stock"],
    responses={404: {"description": "Not found"}},
)


@router.get("/statistics", response_model=Dict)
async def get_capital_statistics(
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get statistics about stock capital data.

    Returns:
        Dictionary containing capital stock statistics including:
        - total_stocks: Total number of stocks in database
        - stocks_with_capital: Number of stocks with capital data
        - stocks_without_capital: Number of stocks without capital data
        - completeness_rate: Percentage of stocks with capital data
        - tse_with_capital: Number of TSE stocks with capital
        - otc_with_capital: Number of OTC stocks with capital
        - last_update: Last update timestamp
        - capital_distribution: Distribution by capital size
    """
    try:
        service = CapitalStockService(db)
        stats = service.get_capital_statistics()

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting capital statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=Dict)
async def update_all_capital_stock(
    db: Session = Depends(get_db)
) -> Dict:
    """
    Update capital stock data for all companies.

    This endpoint fetches the latest capital data from government open data platforms
    for both TSE (上市) and OTC (上櫃) companies and updates the database.

    Returns:
        Dictionary with update statistics:
        - total_fetched: Total number of companies fetched
        - updated_count: Number of existing stocks updated
        - new_count: Number of new stocks added
        - error_count: Number of errors encountered
        - listed_count: Number of TSE companies
        - otc_count: Number of OTC companies
    """
    try:
        service = CapitalStockService(db)
        stats = await service.update_all_capital_stock()

        return {
            "status": "success",
            "message": f"Successfully updated capital data for {stats['updated_count']} stocks",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error updating capital stock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}", response_model=Dict)
async def get_stock_capital(
    stock_code: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get capital data for a specific stock.

    Args:
        stock_code: The stock code (e.g., "2330" for TSMC)

    Returns:
        Dictionary containing:
        - stock_code: Stock code
        - stock_name: Company name
        - market: Market (TSE/TPEx)
        - industry: Industry category
        - capital_stock: Capital amount in NTD
        - capital_stock_billion: Capital amount in billions NTD
        - capital_updated_at: Last update timestamp
        - capital_category: Category (大型股/中型股/小型股)
    """
    try:
        # 驗證股票代號格式
        if not stock_code.isdigit() or len(stock_code) != 4:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stock code format: {stock_code}. Must be 4 digits."
            )

        service = CapitalStockService(db)
        capital_data = service.get_stock_capital(stock_code)

        if not capital_data:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {stock_code} not found"
            )

        return {
            "status": "success",
            "data": capital_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting capital for stock {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/completeness", response_model=Dict)
async def check_capital_completeness(
    db: Session = Depends(get_db)
) -> Dict:
    """
    Check the completeness of capital stock data.

    This endpoint provides a quick check of how many stocks have capital data
    and identifies stocks that are missing capital information.

    Returns:
        Dictionary containing:
        - has_capital: List of stock codes with capital data
        - missing_capital: List of stock codes without capital data
        - summary: Summary statistics
    """
    try:
        from src.models.stock import Stock

        # 查詢有股本資料的股票
        stocks_with_capital = db.query(Stock.stock_code, Stock.stock_name).filter(
            Stock.capital_stock.isnot(None),
            Stock.capital_stock > 0
        ).all()

        # 查詢沒有股本資料的股票
        stocks_without_capital = db.query(Stock.stock_code, Stock.stock_name).filter(
            or_(
                Stock.capital_stock.is_(None),
                Stock.capital_stock == 0
            )
        ).all()

        return {
            "status": "success",
            "data": {
                "has_capital": [
                    {"stock_code": s.stock_code, "stock_name": s.stock_name}
                    for s in stocks_with_capital[:10]  # 只顯示前10筆
                ],
                "missing_capital": [
                    {"stock_code": s.stock_code, "stock_name": s.stock_name}
                    for s in stocks_without_capital[:10]  # 只顯示前10筆
                ],
                "summary": {
                    "total_with_capital": len(stocks_with_capital),
                    "total_without_capital": len(stocks_without_capital),
                    "completeness_rate": round(
                        len(stocks_with_capital) /
                        (len(stocks_with_capital) + len(stocks_without_capital)) * 100,
                        2
                    ) if (len(stocks_with_capital) + len(stocks_without_capital)) > 0 else 0
                }
            }
        }

    except Exception as e:
        logger.error(f"Error checking capital completeness: {e}")
        raise HTTPException(status_code=500, detail=str(e))