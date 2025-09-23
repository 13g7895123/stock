"""證交所官方API資料服務 - Taiwan Stock Exchange Official API Data Service."""

import logging
import math
import pandas as pd
import numpy as np
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from src.models.stock import StockDailyData

logger = logging.getLogger(__name__)


class TwseDataService:
    """證交所官方API資料服務類別。"""

    def __init__(self, db_session: Session = None):
        """初始化證交所資料服務。"""
        self.db_session = db_session
        self.timeout = httpx.Timeout(30.0)
        self.base_url = "https://www.twse.com.tw"

    async def fetch_daily_all_stocks(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        從證交所API獲取指定日期的所有股票交易資料。

        Args:
            target_date: 目標日期，格式為 YYYYMMDD，如 "20240920"。如為 None 則獲取當日資料。

        Returns:
            Dict containing status and data or error information
        """
        try:
            date_desc = f"指定日期 {target_date}" if target_date else "當日"
            logger.info(f"開始從證交所API獲取{date_desc}所有股票資料")

            # 證交所每日成交資訊API端點
            if target_date:
                # 歷史資料查詢
                url = f"{self.base_url}/exchangeReport/STOCK_DAY_ALL?response=json&date={target_date}"
            else:
                # 當日資料查詢
                url = f"{self.base_url}/exchangeReport/STOCK_DAY_ALL?response=open_data"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                # 檢查回應內容類型
                content_type = response.headers.get('content-type', '')
                if 'text/csv' not in content_type and 'application/csv' not in content_type:
                    logger.warning(f"意外的內容類型: {content_type}")

                # 使用pandas讀取CSV資料
                try:
                    # 將回應內容轉為DataFrame
                    from io import StringIO
                    csv_data = StringIO(response.text)
                    df = pd.read_csv(csv_data)

                    logger.info(f"成功從證交所獲取 {len(df)} 筆股票資料")

                    # 清理 DataFrame 中的無效數值
                    # 將 inf 和 -inf 替換為 None
                    df = df.replace([np.inf, -np.inf], np.nan)
                    # 將 NaN 替換為 None (JSON 可以序列化 None)
                    df = df.where(pd.notnull(df), None)

                    # 轉換為字典格式
                    stocks_data = df.to_dict('records')

                    # 額外的數據清理 - 確保每個值都是 JSON 可序列化的
                    cleaned_stocks_data = []
                    for stock in stocks_data:
                        cleaned_stock = {}
                        for key, value in stock.items():
                            # 檢查並清理數值
                            if isinstance(value, (float, np.float64, np.float32)):
                                if math.isnan(value) or math.isinf(value):
                                    cleaned_stock[key] = None
                                else:
                                    cleaned_stock[key] = float(value)
                            elif isinstance(value, (np.int64, np.int32)):
                                cleaned_stock[key] = int(value)
                            else:
                                cleaned_stock[key] = value
                        cleaned_stocks_data.append(cleaned_stock)

                    return {
                        "status": "success",
                        "data": cleaned_stocks_data,
                        "total_records": len(cleaned_stocks_data),
                        "source": "證交所官方API",
                        "timestamp": datetime.now().isoformat(),
                        "columns": list(df.columns)
                    }

                except Exception as parse_error:
                    logger.error(f"解析證交所CSV資料失敗: {parse_error}")
                    return {
                        "status": "error",
                        "error": f"資料解析失敗: {str(parse_error)}",
                        "raw_content_preview": response.text[:500] if response.text else "無內容"
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"證交所API HTTP錯誤: {e.response.status_code} - {e.response.text}")
            return {
                "status": "error",
                "error": f"HTTP錯誤 {e.response.status_code}: {e.response.text}"
            }
        except httpx.RequestError as e:
            logger.error(f"證交所API請求錯誤: {e}")
            return {
                "status": "error",
                "error": f"網路請求失敗: {str(e)}"
            }
        except Exception as e:
            logger.error(f"證交所API意外錯誤: {e}")
            return {
                "status": "error",
                "error": f"未預期的錯誤: {str(e)}"
            }

    async def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        從證交所API獲取特定股票的交易資料。

        Args:
            symbol: 股票代號 (4位數字)

        Returns:
            Dict containing stock data or error information
        """
        try:
            # 驗證股票代號格式
            if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
                return {
                    "status": "error",
                    "error": f"無效的股票代號格式: {symbol}. 必須是4位數字且不能以0開頭"
                }

            logger.info(f"從證交所API獲取股票 {symbol} 的資料")

            # 先獲取所有股票資料
            all_stocks_result = await self.fetch_daily_all_stocks()

            if all_stocks_result["status"] != "success":
                return all_stocks_result

            # 從所有資料中篩選出指定股票
            stocks_data = all_stocks_result["data"]
            stock_data = None

            # 尋找指定股票代號的資料
            for stock in stocks_data:
                # 檢查證券代號欄位 (可能的欄位名稱)
                stock_code = stock.get('證券代號') or stock.get('股票代號') or stock.get('Symbol') or stock.get('Code')
                if stock_code and str(stock_code).strip() == symbol:
                    stock_data = stock
                    break

            if stock_data:
                logger.info(f"成功找到股票 {symbol} 的資料")
                return {
                    "status": "success",
                    "stock_code": symbol,
                    "data": stock_data,
                    "source": "證交所官方API",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"在證交所資料中找不到股票 {symbol}")
                return {
                    "status": "not_found",
                    "stock_code": symbol,
                    "error": f"股票 {symbol} 在證交所當日資料中未找到",
                    "available_columns": all_stocks_result.get("columns", [])
                }

        except Exception as e:
            logger.error(f"獲取股票 {symbol} 資料時發生錯誤: {e}")
            return {
                "status": "error",
                "stock_code": symbol,
                "error": f"處理股票資料時發生錯誤: {str(e)}"
            }

    def save_stock_data_to_database(self, stock_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        將證交所股票資料儲存到資料庫。

        Args:
            stock_data: 股票資料字典
            symbol: 股票代號

        Returns:
            Dict containing save result
        """
        try:
            if not self.db_session:
                return {
                    "status": "error",
                    "error": "資料庫連線未設定"
                }

            logger.info(f"將股票 {symbol} 的證交所資料儲存到資料庫")

            # 解析股票資料欄位 (根據證交所實際欄位名稱調整)
            # 注意：需要根據實際證交所API回傳的欄位名稱進行調整
            parsed_data = self._parse_twse_stock_data(stock_data, symbol)

            if not parsed_data:
                return {
                    "status": "error",
                    "error": "無法解析證交所資料格式"
                }

            # 檢查資料庫中是否已存在相同日期的資料
            existing_record = self.db_session.query(StockDailyData).filter(
                StockDailyData.stock_code == symbol,
                StockDailyData.trade_date == parsed_data["trade_date"]
            ).first()

            if existing_record:
                # 更新現有記錄
                for key, value in parsed_data.items():
                    if hasattr(existing_record, key):
                        setattr(existing_record, key, value)

                self.db_session.commit()
                logger.info(f"更新股票 {symbol} 的資料庫記錄")
                return {
                    "status": "success",
                    "action": "updated",
                    "stock_code": symbol,
                    "trade_date": parsed_data["trade_date"]
                }
            else:
                # 新增記錄
                new_record = StockDailyData(**parsed_data)
                self.db_session.add(new_record)
                self.db_session.commit()
                logger.info(f"新增股票 {symbol} 的資料庫記錄")
                return {
                    "status": "success",
                    "action": "created",
                    "stock_code": symbol,
                    "trade_date": parsed_data["trade_date"]
                }

        except Exception as e:
            if self.db_session:
                self.db_session.rollback()
            logger.error(f"儲存股票 {symbol} 資料到資料庫時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"資料庫操作失敗: {str(e)}"
            }

    def _parse_twse_stock_data(self, stock_data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        解析證交所股票資料格式。

        Args:
            stock_data: 原始證交所資料
            symbol: 股票代號

        Returns:
            解析後的資料字典，符合資料庫模型格式
        """
        try:
            # 根據證交所實際API欄位名稱進行映射
            # 注意：這些欄位名稱需要根據實際API回應進行調整

            # 常見的證交所欄位名稱映射
            field_mapping = {
                '證券代號': 'stock_code',
                '證券名稱': 'stock_name',
                '成交股數': 'volume',
                '成交金額': 'turnover',
                '開盤價': 'open_price',
                '最高價': 'high_price',
                '最低價': 'low_price',
                '收盤價': 'close_price',
                '漲跌價差': 'price_change',
                '成交筆數': 'transaction_count'
            }

            parsed_data = {
                'stock_code': symbol,
                'trade_date': date.today(),  # 使用今日日期
                'data_source': 'twse_api'
            }

            # 映射欄位
            for twse_field, db_field in field_mapping.items():
                if twse_field in stock_data:
                    value = stock_data[twse_field]

                    # 數值型欄位處理
                    if db_field in ['volume', 'turnover', 'open_price', 'high_price', 'low_price', 'close_price', 'price_change', 'transaction_count']:
                        try:
                            # 移除逗號和其他非數字字符
                            if isinstance(value, str):
                                value = value.replace(',', '').replace('--', '0').strip()
                                # 處理空白或特殊符號
                                if value == '' or value == '--' or value == 'N/A':
                                    parsed_data[db_field] = 0.0
                                else:
                                    # 嘗試轉換為浮點數
                                    float_value = float(value)
                                    # 檢查是否為有效的數值（非無限大和非NaN）
                                    if math.isnan(float_value) or math.isinf(float_value):
                                        logger.warning(f"股票 {symbol} 的 {db_field} 包含無效數值: {value}")
                                        parsed_data[db_field] = 0.0
                                    else:
                                        parsed_data[db_field] = float_value
                            elif isinstance(value, (int, float)):
                                # 檢查數值是否有效
                                if math.isnan(value) or math.isinf(value):
                                    logger.warning(f"股票 {symbol} 的 {db_field} 包含無效數值")
                                    parsed_data[db_field] = 0.0
                                else:
                                    parsed_data[db_field] = float(value)
                            else:
                                parsed_data[db_field] = 0.0
                        except (ValueError, TypeError, OverflowError) as e:
                            logger.warning(f"轉換 {db_field} 時發生錯誤: {e}, 原始值: {value}")
                            parsed_data[db_field] = 0.0
                    else:
                        parsed_data[db_field] = str(value) if value is not None else ''

            # 驗證必要欄位
            required_fields = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
            for field in required_fields:
                if field not in parsed_data or parsed_data[field] <= 0:
                    logger.warning(f"股票 {symbol} 缺少或無效的必要欄位: {field}")
                    return None

            return parsed_data

        except Exception as e:
            logger.error(f"解析股票 {symbol} 的證交所資料時發生錯誤: {e}")
            return None

    async def get_market_summary(self) -> Dict[str, Any]:
        """
        獲取市場總體統計資訊。

        Returns:
            Dict containing market summary data
        """
        try:
            logger.info("獲取證交所市場總體統計資訊")

            # 獲取所有股票資料
            all_stocks_result = await self.fetch_daily_all_stocks()

            if all_stocks_result["status"] != "success":
                return all_stocks_result

            stocks_data = all_stocks_result["data"]

            # 計算市場統計
            total_stocks = len(stocks_data)

            # 統計漲跌家數 (根據實際欄位調整)
            rising_count = 0
            falling_count = 0
            unchanged_count = 0

            total_volume = 0
            total_turnover = 0

            for stock in stocks_data:
                # 統計成交量和成交金額
                try:
                    volume = stock.get('成交股數', 0)
                    turnover = stock.get('成交金額', 0)

                    # 處理成交股數
                    if isinstance(volume, str):
                        cleaned_volume = volume.replace(',', '').replace('--', '0').strip()
                        if cleaned_volume and cleaned_volume != 'N/A':
                            try:
                                volume = float(cleaned_volume)
                                if math.isnan(volume) or math.isinf(volume):
                                    volume = 0
                            except (ValueError, OverflowError):
                                volume = 0
                        else:
                            volume = 0
                    elif isinstance(volume, (int, float)):
                        if math.isnan(volume) or math.isinf(volume):
                            volume = 0
                    else:
                        volume = 0

                    # 處理成交金額
                    if isinstance(turnover, str):
                        cleaned_turnover = turnover.replace(',', '').replace('--', '0').strip()
                        if cleaned_turnover and cleaned_turnover != 'N/A':
                            try:
                                turnover = float(cleaned_turnover)
                                if math.isnan(turnover) or math.isinf(turnover):
                                    turnover = 0
                            except (ValueError, OverflowError):
                                turnover = 0
                        else:
                            turnover = 0
                    elif isinstance(turnover, (int, float)):
                        if math.isnan(turnover) or math.isinf(turnover):
                            turnover = 0
                    else:
                        turnover = 0

                    total_volume += volume
                    total_turnover += turnover

                    # 統計漲跌 (根據漲跌價差或其他欄位)
                    price_change = stock.get('漲跌價差', 0)
                    if isinstance(price_change, str):
                        # 移除正負號和逗號
                        cleaned_price = price_change.replace(',', '').replace('+', '').strip()
                        if cleaned_price.startswith('-'):
                            is_negative = True
                            cleaned_price = cleaned_price[1:]
                        else:
                            is_negative = False

                        if cleaned_price and cleaned_price != '--' and cleaned_price != 'N/A':
                            try:
                                price_change = float(cleaned_price)
                                if is_negative:
                                    price_change = -price_change
                                if math.isnan(price_change) or math.isinf(price_change):
                                    price_change = 0
                            except (ValueError, OverflowError):
                                price_change = 0
                        else:
                            price_change = 0
                    elif isinstance(price_change, (int, float)):
                        if math.isnan(price_change) or math.isinf(price_change):
                            price_change = 0

                    if price_change > 0:
                        rising_count += 1
                    elif price_change < 0:
                        falling_count += 1
                    else:
                        unchanged_count += 1

                except (ValueError, TypeError, OverflowError) as e:
                    logger.warning(f"處理股票統計時發生錯誤: {e}")
                    unchanged_count += 1
                    continue

            return {
                "status": "success",
                "summary": {
                    "total_stocks": total_stocks,
                    "rising_stocks": rising_count,
                    "falling_stocks": falling_count,
                    "unchanged_stocks": unchanged_count,
                    "total_volume": total_volume,
                    "total_turnover": total_turnover
                },
                "source": "證交所官方API",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"獲取市場統計資訊時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"無法獲取市場統計: {str(e)}"
            }

    async def fetch_historical_stock_data(self, symbol: str, target_date: str) -> Dict[str, Any]:
        """
        從證交所API獲取特定股票的歷史資料。

        Args:
            symbol: 股票代號 (4位數字)
            target_date: 目標日期，格式為 YYYYMMDD，如 "20240920"

        Returns:
            Dict containing historical stock data or error information
        """
        try:
            # 驗證股票代號格式
            if not symbol or len(symbol) != 4 or not symbol.isdigit() or symbol.startswith("0"):
                return {
                    "status": "error",
                    "error": f"無效的股票代號格式: {symbol}. 必須是4位數字且不能以0開頭"
                }

            # 驗證日期格式
            if not target_date or len(target_date) != 8 or not target_date.isdigit():
                return {
                    "status": "error",
                    "error": f"無效的日期格式: {target_date}. 必須是8位數字，格式為YYYYMMDD"
                }

            logger.info(f"從證交所API獲取股票 {symbol} 在 {target_date} 的歷史資料")

            # 證交所個股日成交資料API端點
            url = f"{self.base_url}/exchangeReport/STOCK_DAY?response=json&date={target_date}&stockNo={symbol}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                # 解析JSON回應
                try:
                    json_data = response.json()

                    # 檢查證交所API回應狀態
                    if json_data.get("stat") != "OK":
                        error_msg = json_data.get("message", "證交所API回應異常")
                        logger.warning(f"證交所API回應: {error_msg}")
                        return {
                            "status": "error",
                            "error": f"證交所API錯誤: {error_msg}",
                            "twse_response": json_data
                        }

                    # 獲取資料欄位和內容
                    fields = json_data.get("fields", [])
                    data = json_data.get("data", [])

                    if not data:
                        logger.warning(f"股票 {symbol} 在 {target_date} 無交易資料")
                        return {
                            "status": "no_data",
                            "stock_code": symbol,
                            "date": target_date,
                            "message": f"股票 {symbol} 在 {target_date} 無交易資料（可能為非交易日）"
                        }

                    # 將資料轉換為易於處理的格式
                    processed_data = []
                    for row in data:
                        if len(row) == len(fields):
                            row_dict = {}
                            for i, field in enumerate(fields):
                                row_dict[field] = row[i]
                            processed_data.append(row_dict)

                    logger.info(f"成功獲取股票 {symbol} 在 {target_date} 的 {len(processed_data)} 筆歷史資料")

                    return {
                        "status": "success",
                        "stock_code": symbol,
                        "date": target_date,
                        "data": processed_data,
                        "fields": fields,
                        "total_records": len(processed_data),
                        "source": "證交所官方API",
                        "timestamp": datetime.now().isoformat(),
                        "api_response": {
                            "title": json_data.get("title", ""),
                            "notes": json_data.get("notes", [])
                        }
                    }

                except Exception as parse_error:
                    logger.error(f"解析證交所歷史資料失敗: {parse_error}")
                    return {
                        "status": "error",
                        "error": f"資料解析失敗: {str(parse_error)}",
                        "raw_content_preview": response.text[:500] if response.text else "無內容"
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"證交所歷史資料API HTTP錯誤: {e.response.status_code} - {e.response.text}")
            return {
                "status": "error",
                "error": f"HTTP錯誤 {e.response.status_code}: {e.response.text}"
            }
        except httpx.RequestError as e:
            logger.error(f"證交所歷史資料API請求錯誤: {e}")
            return {
                "status": "error",
                "error": f"網路請求失敗: {str(e)}"
            }
        except Exception as e:
            logger.error(f"證交所歷史資料API意外錯誤: {e}")
            return {
                "status": "error",
                "error": f"未預期的錯誤: {str(e)}"
            }

    async def fetch_historical_all_stocks(self, target_date: str) -> Dict[str, Any]:
        """
        從證交所API獲取指定日期的所有股票交易資料。

        Args:
            target_date: 目標日期，格式為 YYYYMMDD，如 "20240920"

        Returns:
            Dict containing all stocks historical data or error information
        """
        try:
            # 驗證日期格式
            if not target_date or len(target_date) != 8 or not target_date.isdigit():
                return {
                    "status": "error",
                    "error": f"無效的日期格式: {target_date}. 必須是8位數字，格式為YYYYMMDD"
                }

            logger.info(f"從證交所API獲取 {target_date} 的所有股票歷史資料")

            # 使用修改後的 fetch_daily_all_stocks 方法
            return await self.fetch_daily_all_stocks(target_date)

        except Exception as e:
            logger.error(f"獲取 {target_date} 所有股票歷史資料時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"處理歷史資料時發生錯誤: {str(e)}"
            }