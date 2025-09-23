"""證交所官方API端點 - Taiwan Stock Exchange Official API Endpoints."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.twse_data_service import TwseDataService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/daily-all", response_model=Dict[str, Any])
async def get_daily_all_stocks(
    date: Optional[str] = Query(None, description="指定日期，格式為YYYYMMDD，如20240920。留空則獲取當日資料"),
    save_to_db: bool = Query(False, description="是否將資料儲存到資料庫"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取證交所指定日期或當日所有股票交易資料。

    - **date**: 指定日期，格式為YYYYMMDD，如20240920。留空則獲取當日資料
    - **save_to_db**: 是否將資料儲存到資料庫 (預設為 False)

    Returns:
        Dict containing all stocks trading data from TWSE
    """
    try:
        date_desc = f"指定日期 {date}" if date else "當日"
        logger.info(f"開始處理證交所{date_desc}所有股票資料請求")

        # 初始化證交所資料服務
        twse_service = TwseDataService(db_session=db)

        # 從證交所API獲取資料
        if date:
            # 驗證日期格式
            if len(date) != 8 or not date.isdigit():
                raise HTTPException(
                    status_code=400,
                    detail=f"無效的日期格式: {date}. 必須是8位數字，格式為YYYYMMDD，如20240920"
                )
            result = await twse_service.fetch_historical_all_stocks(date)
        else:
            result = await twse_service.fetch_daily_all_stocks()

        if result["status"] != "success":
            logger.error(f"證交所API獲取失敗: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=503,
                detail=f"證交所API暫時無法使用: {result.get('error', '未知錯誤')}"
            )

        # 如果需要儲存到資料庫
        saved_count = 0
        if save_to_db and result.get("data"):
            logger.info("開始將證交所資料儲存到資料庫")
            for stock_data in result["data"]:
                try:
                    # 從資料中取得股票代號
                    stock_code = stock_data.get('證券代號') or stock_data.get('股票代號') or stock_data.get('Symbol')
                    if stock_code and len(str(stock_code).strip()) == 4:
                        save_result = twse_service.save_stock_data_to_database(stock_data, str(stock_code).strip())
                        if save_result["status"] == "success":
                            saved_count += 1
                except Exception as save_error:
                    logger.warning(f"儲存股票資料時發生錯誤: {save_error}")
                    continue

        # 準備回應
        response = {
            "status": "success",
            "message": "成功獲取證交所當日所有股票交易資料",
            "data": result["data"],
            "metadata": {
                "total_records": result.get("total_records", len(result["data"])),
                "source": result.get("source", "證交所官方API"),
                "timestamp": result.get("timestamp"),
                "columns": result.get("columns", []),
                "saved_to_database": saved_count if save_to_db else None
            }
        }

        logger.info(f"成功回傳 {response['metadata']['total_records']} 筆證交所股票資料")
        if save_to_db:
            logger.info(f"已儲存 {saved_count} 筆資料到資料庫")

        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理證交所所有股票資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/stock/{symbol}", response_model=Dict[str, Any])
async def get_stock_data(
    symbol: str,
    save_to_db: bool = Query(False, description="是否將資料儲存到資料庫"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取證交所特定股票的當日交易資料。

    - **symbol**: 股票代號 (4位數字，不以0開頭)
    - **save_to_db**: 是否將資料儲存到資料庫 (預設為 False)

    Returns:
        Dict containing specific stock trading data from TWSE
    """
    try:
        # 驗證股票代號格式
        if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
            raise HTTPException(
                status_code=400,
                detail=f"無效的股票代號: {symbol}. 必須是4位數字且不能以0開頭"
            )

        logger.info(f"開始處理股票 {symbol} 的證交所資料請求")

        # 初始化證交所資料服務
        twse_service = TwseDataService(db_session=db)

        # 從證交所API獲取特定股票資料
        result = await twse_service.fetch_stock_data(symbol)

        if result["status"] == "error":
            logger.error(f"獲取股票 {symbol} 資料失敗: {result.get('error')}")
            raise HTTPException(
                status_code=503,
                detail=f"證交所API暫時無法使用: {result.get('error', '未知錯誤')}"
            )
        elif result["status"] == "not_found":
            logger.warning(f"在證交所當日資料中找不到股票 {symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"股票 {symbol} 在證交所當日交易資料中未找到"
            )

        # 如果需要儲存到資料庫
        save_result = None
        if save_to_db and result.get("data"):
            logger.info(f"將股票 {symbol} 的證交所資料儲存到資料庫")
            save_result = twse_service.save_stock_data_to_database(result["data"], symbol)
            if save_result["status"] != "success":
                logger.warning(f"儲存股票 {symbol} 資料到資料庫失敗: {save_result.get('error')}")

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功獲取股票 {symbol} 的證交所當日交易資料",
            "stock_code": symbol,
            "data": result["data"],
            "metadata": {
                "source": result.get("source", "證交所官方API"),
                "timestamp": result.get("timestamp"),
                "database_saved": save_result["status"] == "success" if save_result else False,
                "database_action": save_result.get("action") if save_result else None
            }
        }

        logger.info(f"成功回傳股票 {symbol} 的證交所資料")
        if save_to_db and save_result:
            logger.info(f"股票 {symbol} 資料已{'儲存' if save_result.get('action') == 'created' else '更新'}到資料庫")

        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理股票 {symbol} 證交所資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/market-summary", response_model=Dict[str, Any])
async def get_market_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取證交所市場總體統計資訊。

    Returns:
        Dict containing market summary statistics
    """
    try:
        logger.info("開始處理證交所市場總體統計請求")

        # 初始化證交所資料服務
        twse_service = TwseDataService(db_session=db)

        # 獲取市場統計資訊
        result = await twse_service.get_market_summary()

        if result["status"] != "success":
            logger.error(f"獲取市場統計失敗: {result.get('error')}")
            raise HTTPException(
                status_code=503,
                detail=f"證交所API暫時無法使用: {result.get('error', '未知錯誤')}"
            )

        # 準備回應
        response = {
            "status": "success",
            "message": "成功獲取證交所市場總體統計資訊",
            "summary": result["summary"],
            "metadata": {
                "source": result.get("source", "證交所官方API"),
                "timestamp": result.get("timestamp"),
                "data_date": datetime.now().strftime("%Y-%m-%d")
            }
        }

        logger.info("成功回傳證交所市場統計資訊")
        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理證交所市場統計時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/info", response_model=Dict[str, Any])
async def get_twse_api_info() -> Dict[str, Any]:
    """
    獲取證交所API服務資訊。

    Returns:
        Dict containing TWSE API service information
    """
    return {
        "service_name": "證交所官方API服務",
        "description": "提供台灣證券交易所官方的每日股票交易資料",
        "features": [
            "當日所有股票交易資料",
            "特定股票交易資料查詢",
            "歷史股票交易資料查詢",
            "指定日期所有股票資料",
            "市場總體統計資訊",
            "資料儲存到資料庫功能"
        ],
        "data_source": "證交所官方API (www.twse.com.tw)",
        "data_fields": [
            "證券代號", "證券名稱", "成交股數", "成交金額",
            "開盤價", "最高價", "最低價", "收盤價",
            "漲跌價差", "成交筆數"
        ],
        "update_frequency": "每日更新",
        "endpoints": {
            "daily_all": "/api/v1/twse/daily-all",
            "daily_all_with_date": "/api/v1/twse/daily-all?date=YYYYMMDD",
            "specific_stock": "/api/v1/twse/stock/{symbol}",
            "historical_stock": "/api/v1/twse/historical/{symbol}?date=YYYYMMDD",
            "historical_all": "/api/v1/twse/historical-all/{date}",
            "market_summary": "/api/v1/twse/market-summary",
            "service_info": "/api/v1/twse/info"
        },
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/historical/{symbol}", response_model=Dict[str, Any])
async def get_historical_stock_data(
    symbol: str,
    date: str = Query(..., description="目標日期，格式為YYYYMMDD，如20240920"),
    save_to_db: bool = Query(False, description="是否將資料儲存到資料庫"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取證交所特定股票的歷史交易資料。

    - **symbol**: 股票代號 (4位數字，不以0開頭)
    - **date**: 目標日期，格式為YYYYMMDD，如20240920
    - **save_to_db**: 是否將資料儲存到資料庫 (預設為 False)

    Returns:
        Dict containing specific stock historical trading data from TWSE

    Examples:
        - 查詢台積電2024年9月20日資料: /twse/historical/2330?date=20240920
        - 查詢鴻海上周五資料: /twse/historical/2317?date=20240913
    """
    try:
        # 驗證股票代號格式
        if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
            raise HTTPException(
                status_code=400,
                detail=f"無效的股票代號: {symbol}. 必須是4位數字且不能以0開頭"
            )

        # 驗證日期格式
        if not date or len(date) != 8 or not date.isdigit():
            raise HTTPException(
                status_code=400,
                detail=f"無效的日期格式: {date}. 必須是8位數字，格式為YYYYMMDD，如20240920"
            )

        logger.info(f"開始處理股票 {symbol} 在 {date} 的歷史資料請求")

        # 初始化證交所資料服務
        twse_service = TwseDataService(db_session=db)

        # 從證交所API獲取歷史資料
        result = await twse_service.fetch_historical_stock_data(symbol, date)

        if result["status"] == "error":
            logger.error(f"獲取股票 {symbol} 歷史資料失敗: {result.get('error')}")
            raise HTTPException(
                status_code=503,
                detail=f"證交所API暫時無法使用: {result.get('error', '未知錯誤')}"
            )
        elif result["status"] == "no_data":
            logger.warning(f"股票 {symbol} 在 {date} 無交易資料")
            raise HTTPException(
                status_code=404,
                detail=f"股票 {symbol} 在 {date} 無交易資料（可能為非交易日或該股票當日未交易）"
            )

        # 如果需要儲存到資料庫
        save_results = []
        if save_to_db and result.get("data"):
            logger.info(f"將股票 {symbol} 在 {date} 的歷史資料儲存到資料庫")
            for daily_data in result["data"]:
                try:
                    save_result = twse_service.save_stock_data_to_database(daily_data, symbol)
                    save_results.append(save_result)
                    if save_result["status"] != "success":
                        logger.warning(f"儲存股票 {symbol} 歷史資料到資料庫失敗: {save_result.get('error')}")
                except Exception as save_error:
                    logger.warning(f"儲存股票 {symbol} 歷史資料時發生錯誤: {save_error}")

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功獲取股票 {symbol} 在 {date} 的歷史交易資料",
            "stock_code": symbol,
            "date": date,
            "data": result["data"],
            "metadata": {
                "fields": result.get("fields", []),
                "total_records": result.get("total_records", len(result["data"])),
                "source": result.get("source", "證交所官方API"),
                "timestamp": result.get("timestamp"),
                "api_response": result.get("api_response", {}),
                "database_operations": save_results if save_to_db else None
            }
        }

        logger.info(f"成功回傳股票 {symbol} 在 {date} 的歷史資料，共 {response['metadata']['total_records']} 筆")
        if save_to_db:
            successful_saves = sum(1 for sr in save_results if sr.get("status") == "success")
            logger.info(f"成功儲存 {successful_saves}/{len(save_results)} 筆歷史資料到資料庫")

        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理股票 {symbol} 在 {date} 的歷史資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/historical-all/{date}", response_model=Dict[str, Any])
async def get_historical_all_stocks_by_date(
    date: str,
    save_to_db: bool = Query(False, description="是否將資料儲存到資料庫"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取證交所指定日期的所有股票交易資料。

    - **date**: 目標日期，格式為YYYYMMDD，如20240920
    - **save_to_db**: 是否將資料儲存到資料庫 (預設為 False)

    Returns:
        Dict containing all stocks historical trading data from TWSE

    Examples:
        - 查詢2024年9月20日所有股票: /twse/historical-all/20240920
        - 查詢上周五所有股票: /twse/historical-all/20240913
    """
    try:
        # 驗證日期格式
        if not date or len(date) != 8 or not date.isdigit():
            raise HTTPException(
                status_code=400,
                detail=f"無效的日期格式: {date}. 必須是8位數字，格式為YYYYMMDD，如20240920"
            )

        logger.info(f"開始處理 {date} 所有股票歷史資料請求")

        # 初始化證交所資料服務
        twse_service = TwseDataService(db_session=db)

        # 從證交所API獲取歷史資料
        result = await twse_service.fetch_historical_all_stocks(date)

        if result["status"] != "success":
            logger.error(f"獲取 {date} 所有股票歷史資料失敗: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=503,
                detail=f"證交所API暫時無法使用: {result.get('error', '未知錯誤')}"
            )

        # 如果需要儲存到資料庫
        saved_count = 0
        if save_to_db and result.get("data"):
            logger.info(f"開始將 {date} 的證交所歷史資料儲存到資料庫")
            for stock_data in result["data"]:
                try:
                    # 從資料中取得股票代號
                    stock_code = stock_data.get('證券代號') or stock_data.get('股票代號') or stock_data.get('Symbol')
                    if stock_code and len(str(stock_code).strip()) == 4:
                        save_result = twse_service.save_stock_data_to_database(stock_data, str(stock_code).strip())
                        if save_result["status"] == "success":
                            saved_count += 1
                except Exception as save_error:
                    logger.warning(f"儲存 {date} 股票資料時發生錯誤: {save_error}")
                    continue

        # 準備回應
        response = {
            "status": "success",
            "message": f"成功獲取 {date} 所有股票歷史交易資料",
            "date": date,
            "data": result["data"],
            "metadata": {
                "total_records": result.get("total_records", len(result["data"])),
                "source": result.get("source", "證交所官方API"),
                "timestamp": result.get("timestamp"),
                "columns": result.get("columns", []),
                "saved_to_database": saved_count if save_to_db else None
            }
        }

        logger.info(f"成功回傳 {date} 的歷史資料，共 {response['metadata']['total_records']} 筆")
        if save_to_db:
            logger.info(f"已儲存 {saved_count} 筆歷史資料到資料庫")

        return response

    except HTTPException:
        # 重新拋出HTTP例外
        raise
    except Exception as e:
        logger.error(f"處理 {date} 所有股票歷史資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )