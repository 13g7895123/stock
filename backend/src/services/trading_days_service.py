"""交易日檢查服務 - Trading Days Analysis Service."""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from src.models.stock import StockDailyData
from src.services.twse_data_service import TwseDataService

logger = logging.getLogger(__name__)


class TradingDaysService:
    """交易日檢查服務類別。"""

    def __init__(self, db_session: Session):
        """初始化交易日檢查服務。"""
        self.db_session = db_session
        self.twse_service = TwseDataService(db_session)

    def get_missing_trading_days_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """
        獲取缺少的交易日統計摘要。

        Args:
            days_back: 檢查過去幾天的資料，預設30天

        Returns:
            Dict containing missing trading days summary
        """
        try:
            logger.info(f"開始檢查過去 {days_back} 天的缺少交易日")

            # 計算日期範圍
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)

            # 獲取資料庫中有資料的日期集合
            existing_dates = self._get_existing_trading_dates(start_date, end_date)

            # 獲取這段期間的潛在交易日（排除週末）
            potential_trading_days = self._get_potential_trading_days(start_date, end_date)

            # 計算缺少的日期
            missing_dates = potential_trading_days - existing_dates

            # 獲取每個缺少日期的統計
            missing_details = []
            for missing_date in sorted(missing_dates):
                detail = self._analyze_missing_date(missing_date)
                missing_details.append(detail)

            # 計算總體統計
            total_potential_days = len(potential_trading_days)
            total_existing_days = len(existing_dates)
            total_missing_days = len(missing_dates)
            completeness_rate = (total_existing_days / total_potential_days * 100) if total_potential_days > 0 else 0

            return {
                "status": "success",
                "summary": {
                    "analysis_period": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "days_analyzed": days_back
                    },
                    "statistics": {
                        "total_potential_trading_days": total_potential_days,
                        "total_existing_days": total_existing_days,
                        "total_missing_days": total_missing_days,
                        "completeness_rate": round(completeness_rate, 2)
                    },
                    "missing_dates": missing_details,
                    "existing_dates": sorted([d.strftime("%Y-%m-%d") for d in existing_dates])
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"檢查缺少交易日時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"無法檢查缺少的交易日: {str(e)}"
            }

    def get_smart_missing_trading_days_analysis(self) -> Dict[str, Any]:
        """
        智能分析缺少的交易日，自動調整檢查範圍。

        Returns:
            Dict containing smart missing trading days analysis
        """
        try:
            logger.info("開始智能分析缺少的交易日")

            # 先獲取最新的交易日期
            latest_trade_date_query = self.db_session.query(
                func.max(func.date(StockDailyData.trade_date)).label('latest_date')
            ).first()

            latest_date = latest_trade_date_query.latest_date if latest_trade_date_query.latest_date else None

            if not latest_date:
                # 如果沒有任何資料，檢查過去30天
                return self.get_missing_trading_days_summary(30)

            # 計算從最新資料日期到今天的天數
            today = date.today()
            days_since_latest = (today - latest_date).days

            # 智能決定檢查範圍
            if days_since_latest <= 7:
                # 如果最新資料在一週內，檢查過去14天
                check_days = 14
            elif days_since_latest <= 30:
                # 如果最新資料在一個月內，檢查過去30天
                check_days = 30
            else:
                # 如果最新資料超過一個月，檢查過去60天
                check_days = 60

            result = self.get_missing_trading_days_summary(check_days)

            # 在結果中添加智能分析資訊
            if result["status"] == "success":
                result["summary"]["smart_analysis"] = {
                    "latest_data_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
                    "days_since_latest_data": days_since_latest,
                    "auto_selected_check_period": check_days,
                    "analysis_reason": self._get_analysis_reason(days_since_latest, check_days)
                }

            return result

        except Exception as e:
            logger.error(f"智能分析缺少交易日時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"無法執行智能分析: {str(e)}"
            }

    def _get_analysis_reason(self, days_since_latest: int, check_days: int) -> str:
        """獲取分析原因說明。"""
        if days_since_latest <= 7:
            return f"最新資料距今 {days_since_latest} 天，檢查過去 {check_days} 天以涵蓋最近的交易日"
        elif days_since_latest <= 30:
            return f"最新資料距今 {days_since_latest} 天，檢查過去 {check_days} 天以評估資料完整性"
        else:
            return f"最新資料距今 {days_since_latest} 天，擴大檢查範圍至 {check_days} 天以全面分析"

    def _get_existing_trading_dates(self, start_date: date, end_date: date) -> Set[date]:
        """獲取資料庫中已存在的交易日期集合。"""
        try:
            # 查詢資料庫中在指定期間內的不重複交易日期
            result = self.db_session.query(
                func.date(StockDailyData.trade_date).label('trade_date')
            ).filter(
                func.date(StockDailyData.trade_date) >= start_date,
                func.date(StockDailyData.trade_date) <= end_date
            ).distinct().all()

            return {row.trade_date for row in result}

        except Exception as e:
            logger.error(f"獲取現有交易日期時發生錯誤: {e}")
            return set()

    def _get_potential_trading_days(self, start_date: date, end_date: date) -> Set[date]:
        """獲取潛在的交易日（排除週末）。"""
        potential_days = set()
        current_date = start_date

        while current_date <= end_date:
            # 排除週末（週六=5, 週日=6）
            if current_date.weekday() < 5:
                potential_days.add(current_date)
            current_date += timedelta(days=1)

        return potential_days

    def _analyze_missing_date(self, missing_date: date) -> Dict[str, Any]:
        """分析特定缺少日期的詳細資訊。"""
        try:
            date_str = missing_date.strftime("%Y-%m-%d")
            weekday = missing_date.strftime("%A")
            weekday_zh = {
                "Monday": "週一", "Tuesday": "週二", "Wednesday": "週三",
                "Thursday": "週四", "Friday": "週五", "Saturday": "週六", "Sunday": "週日"
            }.get(weekday, weekday)

            # 檢查是否為最近幾天（可能還未更新）
            days_ago = (date.today() - missing_date).days
            is_recent = days_ago <= 2

            # 分析可能的原因
            reasons = []
            if is_recent:
                reasons.append("可能為最近交易日，資料尚未更新")
            if missing_date.weekday() >= 5:
                reasons.append("週末非交易日")
            else:
                reasons.append("可能為國定假日或證交所休市日")

            return {
                "date": date_str,
                "weekday": weekday_zh,
                "days_ago": days_ago,
                "is_recent": is_recent,
                "possible_reasons": reasons,
                "is_weekend": missing_date.weekday() >= 5
            }

        except Exception as e:
            logger.error(f"分析缺少日期 {missing_date} 時發生錯誤: {e}")
            return {
                "date": missing_date.strftime("%Y-%m-%d"),
                "error": str(e)
            }

    def get_stock_missing_data_summary(self, stock_code: str = None, days_back: int = 30) -> Dict[str, Any]:
        """
        獲取特定股票或所有股票的缺少資料統計。

        Args:
            stock_code: 股票代號，如為None則分析所有股票
            days_back: 檢查過去幾天的資料

        Returns:
            Dict containing stock-specific missing data analysis
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)

            if stock_code:
                # 分析特定股票
                return self._analyze_single_stock_missing_data(stock_code, start_date, end_date)
            else:
                # 分析所有股票的資料完整性
                return self._analyze_all_stocks_missing_data(start_date, end_date)

        except Exception as e:
            logger.error(f"獲取股票缺少資料統計時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"無法獲取股票資料統計: {str(e)}"
            }

    def _analyze_single_stock_missing_data(self, stock_code: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """分析單一股票的缺少資料。"""
        try:
            # 獲取該股票在指定期間的交易日期
            stock_dates = self.db_session.query(
                func.date(StockDailyData.trade_date).label('trade_date')
            ).filter(
                StockDailyData.stock_code == stock_code,
                func.date(StockDailyData.trade_date) >= start_date,
                func.date(StockDailyData.trade_date) <= end_date
            ).distinct().all()

            stock_trading_dates = {row.trade_date for row in stock_dates}

            # 獲取系統中所有的交易日期
            all_trading_dates = self._get_existing_trading_dates(start_date, end_date)

            # 計算該股票缺少的交易日
            missing_dates = all_trading_dates - stock_trading_dates

            return {
                "status": "success",
                "stock_code": stock_code,
                "analysis": {
                    "period": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    },
                    "statistics": {
                        "total_trading_days": len(all_trading_dates),
                        "stock_has_data_days": len(stock_trading_dates),
                        "missing_days": len(missing_dates),
                        "completeness_rate": round((len(stock_trading_dates) / len(all_trading_dates) * 100) if all_trading_dates else 0, 2)
                    },
                    "missing_dates": sorted([d.strftime("%Y-%m-%d") for d in missing_dates])
                }
            }

        except Exception as e:
            logger.error(f"分析股票 {stock_code} 缺少資料時發生錯誤: {e}")
            return {
                "status": "error",
                "stock_code": stock_code,
                "error": str(e)
            }

    def _analyze_all_stocks_missing_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """分析所有股票的資料完整性。"""
        try:
            # 獲取所有股票的資料完整性統計
            query = text("""
                SELECT
                    stock_code,
                    COUNT(DISTINCT DATE(trade_date)) as days_with_data
                FROM stock_daily_data
                WHERE DATE(trade_date) >= :start_date
                    AND DATE(trade_date) <= :end_date
                GROUP BY stock_code
                ORDER BY days_with_data DESC
            """)

            result = self.db_session.execute(query, {
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()

            # 獲取所有可能的交易日數量
            all_trading_dates = self._get_existing_trading_dates(start_date, end_date)
            total_trading_days = len(all_trading_dates)

            # 統計分析
            stock_completeness = []
            for row in result:
                completeness_rate = (row.days_with_data / total_trading_days * 100) if total_trading_days > 0 else 0
                stock_completeness.append({
                    "stock_code": row.stock_code,
                    "days_with_data": row.days_with_data,
                    "missing_days": total_trading_days - row.days_with_data,
                    "completeness_rate": round(completeness_rate, 2)
                })

            # 計算整體統計
            total_stocks = len(stock_completeness)
            fully_complete_stocks = sum(1 for s in stock_completeness if s["completeness_rate"] >= 100)
            avg_completeness = sum(s["completeness_rate"] for s in stock_completeness) / total_stocks if total_stocks > 0 else 0

            return {
                "status": "success",
                "analysis": {
                    "period": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    },
                    "overall_statistics": {
                        "total_trading_days": total_trading_days,
                        "total_stocks_analyzed": total_stocks,
                        "fully_complete_stocks": fully_complete_stocks,
                        "average_completeness_rate": round(avg_completeness, 2)
                    },
                    "stock_completeness": stock_completeness[:50]  # 限制返回前50個股票
                }
            }

        except Exception as e:
            logger.error(f"分析所有股票資料完整性時發生錯誤: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def suggest_missing_data_fixes(self, missing_dates: List[str]) -> Dict[str, Any]:
        """
        對缺少的交易日提供修復建議。

        Args:
            missing_dates: 缺少的日期列表，格式為 YYYY-MM-DD

        Returns:
            Dict containing suggestions for fixing missing data
        """
        try:
            suggestions = []

            for date_str in missing_dates:
                try:
                    # 轉換日期格式以符合證交所API
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    twse_date_format = date_obj.strftime("%Y%m%d")

                    # 檢查是否為最近日期
                    days_ago = (date.today() - date_obj).days

                    suggestion = {
                        "date": date_str,
                        "twse_api_date": twse_date_format,
                        "days_ago": days_ago,
                        "suggested_actions": []
                    }

                    if days_ago <= 2:
                        suggestion["suggested_actions"].append({
                            "action": "等待自動更新",
                            "description": "最近的交易日，系統可能尚未更新資料",
                            "priority": "low"
                        })
                    else:
                        suggestion["suggested_actions"].append({
                            "action": "手動更新",
                            "description": f"使用證交所API手動獲取 {date_str} 的資料",
                            "api_endpoint": f"/api/v1/twse/historical-all/{twse_date_format}",
                            "priority": "high"
                        })

                    suggestions.append(suggestion)

                except ValueError as e:
                    logger.warning(f"無效的日期格式: {date_str}, 錯誤: {e}")
                    continue

            return {
                "status": "success",
                "suggestions": suggestions,
                "summary": {
                    "total_missing_dates": len(missing_dates),
                    "actionable_suggestions": len(suggestions)
                }
            }

        except Exception as e:
            logger.error(f"生成缺少資料修復建議時發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"無法生成修復建議: {str(e)}"
            }