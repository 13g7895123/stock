"""Service for fetching and managing institutional trading data (投信外資買賣超)."""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import re

import httpx
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.stock import InstitutionalTradingData

logger = logging.getLogger(__name__)


class InstitutionalTradingService:
    """Service for managing institutional trading data."""

    # 證交所三大法人買賣超API
    TWSE_T86_URL = "https://www.twse.com.tw/fund/T86"

    def __init__(self, db: Session = None):
        """Initialize the service."""
        self.db = db or next(get_db())

    async def fetch_institutional_trading_data(self, target_date: str) -> Dict:
        """
        從證交所 T86 API 獲取三大法人買賣超資料。

        Args:
            target_date: 目標日期，格式 YYYYMMDD

        Returns:
            包含API回應資料的字典
        """
        try:
            params = {
                "response": "json",
                "date": target_date,
                "selectType": "ALL"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(self.TWSE_T86_URL, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("stat") != "OK":
                    status = data.get("stat", "Unknown")
                    # Handle both English and Chinese "no data" responses
                    if status in ["No Data!", "很抱歉，沒有符合條件的資料!"]:
                        logger.info(f"No institutional trading data available for date {target_date} (Status: {status})")
                        return {
                            "status": "success",
                            "no_data": True,
                            "date": target_date,
                            "message": f"No institutional trading data available for {target_date}",
                            "data": [],
                            "total_records": 0
                        }
                    else:
                        logger.warning(f"TWSE API returned status: {status} for date {target_date}")
                        return {"status": "error", "message": f"TWSE API error: {status}"}

                logger.info(f"Successfully fetched institutional trading data for {target_date}, records: {len(data.get('data', []))}")
                return {
                    "status": "success",
                    "date": data.get("date"),
                    "title": data.get("title"),
                    "fields": data.get("fields"),
                    "data": data.get("data"),
                    "total_records": len(data.get("data", []))
                }

        except Exception as e:
            logger.error(f"Error fetching institutional trading data for {target_date}: {e}")
            return {"status": "error", "message": str(e)}

    def parse_and_save_institutional_data(self, api_data: Dict, target_date: str) -> Dict:
        """
        解析API資料並儲存到資料庫。

        Args:
            api_data: API回應資料
            target_date: 目標日期 YYYYMMDD

        Returns:
            儲存結果統計
        """
        if api_data.get("status") != "success":
            return {"status": "error", "message": "Invalid API data"}

        try:
            # 轉換日期格式
            trade_date = datetime.strptime(target_date, "%Y%m%d").date()

            data_records = api_data.get("data", [])

            stats = {
                "total_processed": 0,
                "created_count": 0,
                "updated_count": 0,
                "error_count": 0,
                "trade_date": target_date
            }

            for record in data_records:
                try:
                    if len(record) < 19:  # 確保有足夠的欄位
                        logger.warning(f"Record has insufficient fields: {len(record)}")
                        stats["error_count"] += 1
                        continue

                    # 解析資料欄位 (依據T86 API的欄位順序)
                    stock_code = record[0].strip()
                    stock_name = record[1].strip()

                    # 驗證股票代號格式
                    if not self._validate_stock_code(stock_code):
                        stats["error_count"] += 1
                        continue

                    # 解析數值欄位並處理千位符號
                    try:
                        foreign_buy = self._parse_number(record[2])
                        foreign_sell = self._parse_number(record[3])
                        foreign_net = self._parse_number(record[4])
                        foreign_dealer_buy = self._parse_number(record[5])
                        foreign_dealer_sell = self._parse_number(record[6])
                        foreign_dealer_net = self._parse_number(record[7])
                        investment_trust_buy = self._parse_number(record[8])
                        investment_trust_sell = self._parse_number(record[9])
                        investment_trust_net = self._parse_number(record[10])
                        dealer_net = self._parse_number(record[11])
                        dealer_self_buy = self._parse_number(record[12])
                        dealer_self_sell = self._parse_number(record[13])
                        dealer_self_net = self._parse_number(record[14])
                        dealer_hedge_buy = self._parse_number(record[15])
                        dealer_hedge_sell = self._parse_number(record[16])
                        dealer_hedge_net = self._parse_number(record[17])
                        total_institutional_net = self._parse_number(record[18])
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing numbers for {stock_code}: {e}")
                        stats["error_count"] += 1
                        continue

                    # 查詢現有記錄
                    existing = self.db.query(InstitutionalTradingData).filter(
                        InstitutionalTradingData.stock_code == stock_code,
                        InstitutionalTradingData.trade_date == trade_date
                    ).first()

                    if existing:
                        # 更新現有記錄
                        existing.stock_name = stock_name
                        existing.foreign_buy = foreign_buy
                        existing.foreign_sell = foreign_sell
                        existing.foreign_net = foreign_net
                        existing.foreign_dealer_buy = foreign_dealer_buy
                        existing.foreign_dealer_sell = foreign_dealer_sell
                        existing.foreign_dealer_net = foreign_dealer_net
                        existing.investment_trust_buy = investment_trust_buy
                        existing.investment_trust_sell = investment_trust_sell
                        existing.investment_trust_net = investment_trust_net
                        existing.dealer_net = dealer_net
                        existing.dealer_self_buy = dealer_self_buy
                        existing.dealer_self_sell = dealer_self_sell
                        existing.dealer_self_net = dealer_self_net
                        existing.dealer_hedge_buy = dealer_hedge_buy
                        existing.dealer_hedge_sell = dealer_hedge_sell
                        existing.dealer_hedge_net = dealer_hedge_net
                        existing.total_institutional_net = total_institutional_net
                        existing.updated_at = datetime.now()
                        stats["updated_count"] += 1
                    else:
                        # 建立新記錄
                        new_record = InstitutionalTradingData(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            trade_date=trade_date,
                            foreign_buy=foreign_buy,
                            foreign_sell=foreign_sell,
                            foreign_net=foreign_net,
                            foreign_dealer_buy=foreign_dealer_buy,
                            foreign_dealer_sell=foreign_dealer_sell,
                            foreign_dealer_net=foreign_dealer_net,
                            investment_trust_buy=investment_trust_buy,
                            investment_trust_sell=investment_trust_sell,
                            investment_trust_net=investment_trust_net,
                            dealer_net=dealer_net,
                            dealer_self_buy=dealer_self_buy,
                            dealer_self_sell=dealer_self_sell,
                            dealer_self_net=dealer_self_net,
                            dealer_hedge_buy=dealer_hedge_buy,
                            dealer_hedge_sell=dealer_hedge_sell,
                            dealer_hedge_net=dealer_hedge_net,
                            total_institutional_net=total_institutional_net
                        )
                        self.db.add(new_record)
                        stats["created_count"] += 1

                    stats["total_processed"] += 1

                except Exception as e:
                    logger.error(f"Error processing record for {record[0] if len(record) > 0 else 'unknown'}: {e}")
                    stats["error_count"] += 1
                    continue

            # 提交變更
            self.db.commit()

            logger.info(
                f"Institutional trading data processing completed for {target_date} - "
                f"Processed: {stats['total_processed']}, "
                f"Created: {stats['created_count']}, "
                f"Updated: {stats['updated_count']}, "
                f"Errors: {stats['error_count']}"
            )

            return {"status": "success", **stats}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in parse_and_save_institutional_data: {e}")
            return {"status": "error", "message": str(e)}

    async def update_institutional_data_for_date(self, target_date: str) -> Dict:
        """
        更新指定日期的投信外資買賣超資料。

        Args:
            target_date: 目標日期 YYYYMMDD

        Returns:
            更新結果
        """
        try:
            # 獲取API資料
            api_data = await self.fetch_institutional_trading_data(target_date)

            if api_data.get("status") != "success":
                return api_data

            # 檢查是否有資料需要處理
            if api_data.get("no_data"):
                # 沒有資料需要處理，返回適當的結果格式
                return {
                    "status": "success",
                    "message": api_data.get("message"),
                    "total_processed": 0,
                    "created_count": 0,
                    "updated_count": 0,
                    "error_count": 0,
                    "trade_date": target_date
                }

            # 解析並儲存資料
            save_result = self.parse_and_save_institutional_data(api_data, target_date)

            return save_result

        except Exception as e:
            logger.error(f"Error updating institutional data for {target_date}: {e}")
            return {"status": "error", "message": str(e)}

    def get_institutional_statistics(self) -> Dict:
        """
        獲取投信外資買賣超資料統計。

        Returns:
            統計資料字典
        """
        try:
            # 總記錄數
            total_records = self.db.query(InstitutionalTradingData).count()

            # 有資料的股票數
            total_stocks = self.db.query(InstitutionalTradingData.stock_code).distinct().count()

            # 最新交易日期
            latest_date = self.db.query(func.max(InstitutionalTradingData.trade_date)).scalar()

            # 最早交易日期
            earliest_date = self.db.query(func.min(InstitutionalTradingData.trade_date)).scalar()

            # 有資料的天數
            total_days = self.db.query(InstitutionalTradingData.trade_date).distinct().count()

            # 最新一日的三大法人統計
            latest_stats = None
            if latest_date:
                latest_summary = self.db.query(
                    func.sum(InstitutionalTradingData.foreign_net).label('foreign_total'),
                    func.sum(InstitutionalTradingData.investment_trust_net).label('trust_total'),
                    func.sum(InstitutionalTradingData.dealer_net).label('dealer_total'),
                    func.sum(InstitutionalTradingData.total_institutional_net).label('total_net')
                ).filter(
                    InstitutionalTradingData.trade_date == latest_date
                ).first()

                latest_stats = {
                    "date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
                    "foreign_net_total": int(latest_summary.foreign_total or 0),
                    "investment_trust_net_total": int(latest_summary.trust_total or 0),
                    "dealer_net_total": int(latest_summary.dealer_total or 0),
                    "total_net": int(latest_summary.total_net or 0)
                }

            return {
                "total_records": total_records,
                "total_stocks": total_stocks,
                "total_days": total_days,
                "earliest_date": earliest_date.strftime("%Y-%m-%d") if earliest_date else None,
                "latest_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
                "latest_summary": latest_stats
            }

        except Exception as e:
            logger.error(f"Error getting institutional statistics: {e}")
            raise

    def get_stock_institutional_data(self, stock_code: str, limit: int = 30) -> Optional[List[Dict]]:
        """
        獲取特定股票的投信外資買賣超資料。

        Args:
            stock_code: 股票代號
            limit: 限制筆數

        Returns:
            股票的投信外資資料列表
        """
        try:
            records = self.db.query(InstitutionalTradingData).filter(
                InstitutionalTradingData.stock_code == stock_code
            ).order_by(
                desc(InstitutionalTradingData.trade_date)
            ).limit(limit).all()

            result = []
            for record in records:
                result.append({
                    "stock_code": record.stock_code,
                    "stock_name": record.stock_name,
                    "trade_date": record.trade_date.strftime("%Y-%m-%d"),
                    "foreign_net": record.foreign_net,
                    "investment_trust_net": record.investment_trust_net,
                    "dealer_net": record.dealer_net,
                    "total_institutional_net": record.total_institutional_net,
                    "foreign_buy": record.foreign_buy,
                    "foreign_sell": record.foreign_sell,
                    "investment_trust_buy": record.investment_trust_buy,
                    "investment_trust_sell": record.investment_trust_sell
                })

            return result

        except Exception as e:
            logger.error(f"Error getting institutional data for stock {stock_code}: {e}")
            return None

    def _validate_stock_code(self, stock_code: str) -> bool:
        """驗證股票代號格式。"""
        if not stock_code:
            return False

        # 移除空白
        stock_code = stock_code.strip()

        # 基本格式檢查：4-6位數字或數字+字母
        if not re.match(r'^[0-9]{4}[A-Z]*$|^[0-9]{5,6}$', stock_code):
            return False

        return True

    def _parse_number(self, value_str: str) -> int:
        """
        解析數字字串，處理千位符號和空值。

        Args:
            value_str: 數字字串

        Returns:
            解析後的整數
        """
        if not value_str or value_str.strip() in ['', '-', 'N/A', '0']:
            return 0

        try:
            # 移除千位符號和空格
            cleaned = value_str.replace(',', '').replace(' ', '').strip()

            # 處理負號
            if cleaned.startswith('-'):
                return -int(cleaned[1:])

            return int(cleaned)

        except (ValueError, TypeError):
            logger.warning(f"Could not parse number: {value_str}")
            return 0

    async def batch_update_institutional_data(self, days_back: int = 30) -> Dict:
        """
        批次更新近期投信外資買賣超資料。

        Args:
            days_back: 回溯天數，預設30天

        Returns:
            批次更新結果統計
        """
        from datetime import datetime, timedelta
        import asyncio

        try:
            end_date = datetime.now()
            results = []
            success_count = 0
            error_count = 0
            no_data_count = 0
            total_processed = 0

            logger.info(f"Starting batch update for institutional data, {days_back} days back")

            for i in range(days_back):
                target_date = (end_date - timedelta(days=i)).strftime("%Y%m%d")
                
                try:
                    logger.info(f"Processing day {i+1}/{days_back}: {target_date}")
                    result = await self.update_institutional_data_for_date(target_date)
                    
                    if result.get("status") == "success":
                        if result.get("no_data"):
                            no_data_count += 1
                        else:
                            success_count += 1
                            total_processed += result.get("total_processed", 0)
                        
                        results.append({
                            "date": target_date,
                            "status": "success",
                            "processed": result.get("total_processed", 0),
                            "created": result.get("created_count", 0),
                            "updated": result.get("updated_count", 0),
                            "no_data": result.get("no_data", False)
                        })
                    else:
                        error_count += 1
                        results.append({
                            "date": target_date,
                            "status": "error",
                            "error": result.get("message", "Unknown error")
                        })

                    # 在請求之間添加短暫延遲，避免過於頻繁的API調用
                    if i < days_back - 1:
                        await asyncio.sleep(0.5)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing date {target_date}: {e}")
                    results.append({
                        "date": target_date,
                        "status": "error",
                        "error": str(e)
                    })

            logger.info(
                f"Batch update completed - Success: {success_count}, "
                f"No Data: {no_data_count}, Errors: {error_count}, "
                f"Total Records: {total_processed}"
            )

            return {
                "status": "success",
                "summary": {
                    "total_days": days_back,
                    "success_count": success_count,
                    "error_count": error_count,
                    "no_data_count": no_data_count,
                    "total_processed": total_processed
                },
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in batch_update_institutional_data: {e}")
            return {"status": "error", "message": str(e)}

    def get_capital_ratio_rankings(self, days_back: int = 30, limit: int = 50) -> Dict:
        """
        獲取指定期間的股本比累積排名。

        Args:
            days_back: 回溯天數
            limit: 限制筆數

        Returns:
            股本比累積排名資料
        """
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc, asc
        from src.models.stock import Stock

        try:
            # 使用資料庫中的最新日期作為結束日期，避免查詢未來日期
            latest_date = self.db.query(func.max(InstitutionalTradingData.trade_date)).scalar()
            if latest_date:
                end_date = latest_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_date = (latest_date - timedelta(days=days_back-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # 如果沒有資料，使用當前日期
                end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
                start_date = (datetime.now() - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)

            # 計算累積股本比
            # 子查詢：計算每個股票在指定期間的累積淨買賣超
            cumulative_subquery = self.db.query(
                InstitutionalTradingData.stock_code,
                InstitutionalTradingData.stock_name,
                func.sum(InstitutionalTradingData.foreign_net).label('foreign_cumulative'),
                func.sum(InstitutionalTradingData.investment_trust_net).label('trust_cumulative'),
                func.sum(InstitutionalTradingData.dealer_net).label('dealer_cumulative'),
                func.sum(InstitutionalTradingData.total_institutional_net).label('total_cumulative'),
                func.count(InstitutionalTradingData.id).label('trading_days')
            ).filter(
                InstitutionalTradingData.trade_date >= start_date,
                InstitutionalTradingData.trade_date <= end_date
            ).group_by(
                InstitutionalTradingData.stock_code,
                InstitutionalTradingData.stock_name
            ).subquery()

            # 主查詢：加入股本資料並計算股本比
            query = self.db.query(
                cumulative_subquery.c.stock_code,
                cumulative_subquery.c.stock_name,
                cumulative_subquery.c.foreign_cumulative,
                cumulative_subquery.c.trust_cumulative,
                cumulative_subquery.c.dealer_cumulative,
                cumulative_subquery.c.total_cumulative,
                cumulative_subquery.c.trading_days,
                Stock.capital_stock
            ).join(
                Stock, cumulative_subquery.c.stock_code == Stock.stock_code, isouter=True
            ).filter(
                Stock.capital_stock.is_not(None),
                Stock.capital_stock > 0,
                cumulative_subquery.c.total_cumulative != 0  # 排除累積淨額為0的記錄
            )

            # 分別取得買超和賣超排名
            # 買超排名 (累積淨額為正)
            buy_rankings = query.filter(
                cumulative_subquery.c.total_cumulative > 0
            ).order_by(desc(cumulative_subquery.c.total_cumulative)).limit(limit).all()

            # 賣超排名 (累積淨額為負)
            sell_rankings = query.filter(
                cumulative_subquery.c.total_cumulative < 0
            ).order_by(asc(cumulative_subquery.c.total_cumulative)).limit(limit).all()

            def calculate_rankings(records, ranking_type):
                result = []
                for idx, record in enumerate(records):
                    # 計算股本比 (累積買賣超金額/股本*100%)
                    capital_ratio = None
                    if record.capital_stock and record.capital_stock > 0:
                        # 股本單位是元，買賣超單位是股數，需要轉換
                        # 假設每股面額為10元（台股標準）
                        # 轉換為 float 類型以避免 decimal 與 float 類型衝突
                        capital_in_shares = float(record.capital_stock) / 10.0
                        capital_ratio = (float(record.total_cumulative) / capital_in_shares) * 100.0 if capital_in_shares > 0 else None

                    result.append({
                        "rank": idx + 1,
                        "stock_code": record.stock_code,
                        "stock_name": record.stock_name,
                        "foreign_cumulative": record.foreign_cumulative,
                        "investment_trust_cumulative": record.trust_cumulative,
                        "dealer_cumulative": record.dealer_cumulative,
                        "total_cumulative": record.total_cumulative,
                        "capital_stock": record.capital_stock,
                        "capital_ratio": round(capital_ratio, 4) if capital_ratio is not None else None,
                        "trading_days": record.trading_days,
                        "ranking_type": ranking_type
                    })
                return result

            return {
                "status": "success",
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days_back
                },
                "buy_rankings": calculate_rankings(buy_rankings, "buy"),
                "sell_rankings": calculate_rankings(sell_rankings, "sell"),
                "buy_count": len(buy_rankings),
                "sell_count": len(sell_rankings)
            }

        except Exception as e:
            logger.error(f"Error getting capital ratio rankings: {e}")
            raise

    def get_daily_capital_ratio_trends(self, days_back: int = 30, top_stocks: int = 10) -> Dict:
        """
        獲取每日股本比趨勢資料，用於圖表顯示。

        Args:
            days_back: 回溯天數
            top_stocks: 顯示前N檔股票

        Returns:
            每日股本比趨勢資料
        """
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc
        from src.models.stock import Stock

        try:
            # 使用資料庫中的最新日期作為結束日期，避免查詢未來日期
            latest_date = self.db.query(func.max(InstitutionalTradingData.trade_date)).scalar()
            if latest_date:
                end_date = latest_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_date = (latest_date - timedelta(days=days_back-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # 如果沒有資料，使用當前日期
                end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
                start_date = (datetime.now() - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)

            # 先獲取累積排名前N的股票
            rankings = self.get_capital_ratio_rankings(days_back, top_stocks)
            if rankings.get("status") != "success":
                return rankings

            # 合併買超和賣超的前幾名
            top_buy_stocks = [stock["stock_code"] for stock in rankings["buy_rankings"][:top_stocks//2]]
            top_sell_stocks = [stock["stock_code"] for stock in rankings["sell_rankings"][:top_stocks//2]]
            target_stocks = top_buy_stocks + top_sell_stocks

            if not target_stocks:
                return {
                    "status": "success",
                    "trends": [],
                    "dates": [],
                    "stocks": []
                }

            # 取得每日資料
            daily_data = self.db.query(
                InstitutionalTradingData.trade_date,
                InstitutionalTradingData.stock_code,
                InstitutionalTradingData.stock_name,
                InstitutionalTradingData.total_institutional_net,
                Stock.capital_stock
            ).join(
                Stock, InstitutionalTradingData.stock_code == Stock.stock_code
            ).filter(
                InstitutionalTradingData.trade_date >= start_date,
                InstitutionalTradingData.trade_date <= end_date,
                InstitutionalTradingData.stock_code.in_(target_stocks),
                Stock.capital_stock.is_not(None),
                Stock.capital_stock > 0
            ).order_by(
                InstitutionalTradingData.trade_date,
                InstitutionalTradingData.stock_code
            ).all()

            # 組織資料結構
            trends_dict = {}
            dates_set = set()

            for record in daily_data:
                date_str = record.trade_date.strftime("%Y-%m-%d")
                dates_set.add(date_str)

                if record.stock_code not in trends_dict:
                    trends_dict[record.stock_code] = {
                        "stock_code": record.stock_code,
                        "stock_name": record.stock_name,
                        "capital_stock": record.capital_stock,
                        "daily_data": {},
                        "cumulative_data": {}
                    }

                # 計算單日股本比
                # 轉換為 float 類型以避免 decimal 與 float 類型衝突
                capital_in_shares = float(record.capital_stock) / 10.0
                daily_ratio = (float(record.total_institutional_net) / capital_in_shares) * 100.0 if capital_in_shares > 0 else 0.0

                trends_dict[record.stock_code]["daily_data"][date_str] = {
                    "net_amount": record.total_institutional_net,
                    "capital_ratio": round(daily_ratio, 4)
                }

            # 計算累積股本比
            dates_list = sorted(list(dates_set))
            
            for stock_code, stock_data in trends_dict.items():
                cumulative_net = 0
                # 轉換為 float 類型以避免 decimal 與 float 類型衝突
                capital_in_shares = float(stock_data["capital_stock"]) / 10.0

                for date_str in dates_list:
                    if date_str in stock_data["daily_data"]:
                        cumulative_net += float(stock_data["daily_data"][date_str]["net_amount"])

                    cumulative_ratio = (cumulative_net / capital_in_shares) * 100.0 if capital_in_shares > 0 else 0.0
                    stock_data["cumulative_data"][date_str] = {
                        "cumulative_net": cumulative_net,
                        "cumulative_ratio": round(cumulative_ratio, 4)
                    }

            return {
                "status": "success",
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days_back
                },
                "dates": dates_list,
                "trends": list(trends_dict.values()),
                "stock_count": len(trends_dict)
            }

        except Exception as e:
            logger.error(f"Error getting daily capital ratio trends: {e}")
            raise