"""股票選股策略服務

根據均線排列進行選股，包括：
1. 完美多頭：MA5 > MA10 > MA20 > MA60 > MA120 > MA240
2. 短線多頭：MA5 > MA10 > MA20
3. 空頭：MA5 < MA10 < MA20 < MA60
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import pandas as pd

from src.models.stock import Stock, StockDailyData, MovingAverages
from src.core.database import get_db

logger = logging.getLogger(__name__)


class StockSelectionService:
    """股票選股策略服務"""

    def __init__(self, db: Session = None):
        """初始化選股服務

        Args:
            db: 資料庫會話
        """
        self.db = db or next(get_db())

    def get_latest_trading_date(self) -> Optional[date]:
        """取得最新交易日期（遇週末往前找）

        Returns:
            最新交易日期
        """
        try:
            # 從均線資料表中取得最新交易日期
            latest_date = self.db.query(
                func.max(MovingAverages.trade_date)
            ).scalar()

            if latest_date:
                return latest_date.date() if hasattr(latest_date, 'date') else latest_date

            # 如果沒有均線資料，從股票日線資料取得
            latest_date = self.db.query(
                func.max(StockDailyData.trade_date)
            ).scalar()

            if latest_date:
                return latest_date.date() if hasattr(latest_date, 'date') else latest_date

            # 如果都沒有資料，返回今天（週末會自動往前找）
            today = date.today()

            # 如果是週六或週日，往前找到週五
            if today.weekday() == 5:  # 週六
                return today - timedelta(days=1)
            elif today.weekday() == 6:  # 週日
                return today - timedelta(days=2)
            else:
                return today

        except Exception as e:
            logger.error(f"取得最新交易日期失敗: {str(e)}")
            return date.today()

    def get_stock_selection_results(
        self,
        selection_date: Optional[date] = None,
        strategy_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """取得選股結果

        Args:
            selection_date: 選股日期，預設為最新交易日
            strategy_types: 策略類型列表，預設為所有策略

        Returns:
            選股結果字典
        """
        try:
            # 如果沒有指定日期，使用最新交易日
            if not selection_date:
                selection_date = self.get_latest_trading_date()

            # 如果沒有指定策略類型，使用所有策略
            if not strategy_types:
                strategy_types = ['perfect_bull', 'short_bull', 'bear']

            results = {
                'selection_date': selection_date.strftime('%Y-%m-%d'),
                'strategies': {}
            }

            # 執行各種策略選股
            if 'perfect_bull' in strategy_types:
                results['strategies']['perfect_bull'] = self._select_perfect_bull(selection_date)

            if 'short_bull' in strategy_types:
                results['strategies']['short_bull'] = self._select_short_bull(selection_date)

            if 'bear' in strategy_types:
                results['strategies']['bear'] = self._select_bear(selection_date)

            # 計算總結統計
            results['summary'] = self._calculate_summary(results['strategies'])

            return results

        except Exception as e:
            logger.error(f"取得選股結果失敗: {str(e)}")
            raise Exception(f"選股失敗: {str(e)}")

    def _select_perfect_bull(self, selection_date: date) -> Dict[str, Any]:
        """選出完美多頭股票

        完美多頭定義：MA5 > MA10 > MA20 > MA60 > MA120 > MA240
        且收盤價 > MA5

        Args:
            selection_date: 選股日期

        Returns:
            完美多頭股票列表
        """
        try:
            # 查詢符合條件的股票
            query = self.db.query(
                MovingAverages.stock_id,
                MovingAverages.ma_5,
                MovingAverages.ma_10,
                MovingAverages.ma_20,
                MovingAverages.ma_60,
                MovingAverages.ma_120,
                MovingAverages.ma_240,
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
                MovingAverages.trade_date == selection_date,
                # 完美多頭條件
                MovingAverages.ma_5 > MovingAverages.ma_10,
                MovingAverages.ma_10 > MovingAverages.ma_20,
                MovingAverages.ma_20 > MovingAverages.ma_60,
                MovingAverages.ma_60 > MovingAverages.ma_120,
                MovingAverages.ma_120 > MovingAverages.ma_240,
                # 收盤價 > MA5
                StockDailyData.close_price > MovingAverages.ma_5,
                # 過濾掉均線資料不完整的股票
                MovingAverages.ma_240.isnot(None),
                MovingAverages.ma_240 > 0
            ).order_by(
                desc(StockDailyData.price_change)
            ).all()

            stocks = []
            for row in query:
                stocks.append({
                    'stock_code': row.stock_id,
                    'stock_name': row.stock_name,
                    'close_price': float(row.close_price),
                    'price_change': float(row.price_change) if row.price_change else 0,
                    'volume': int(row.volume),
                    'ma_5': float(row.ma_5),
                    'ma_10': float(row.ma_10),
                    'ma_20': float(row.ma_20),
                    'ma_60': float(row.ma_60),
                    'ma_120': float(row.ma_120),
                    'ma_240': float(row.ma_240),
                    'ma_bias': round((float(row.close_price) - float(row.ma_5)) / float(row.ma_5) * 100, 2)  # 5日均線乖離率
                })

            return {
                'name': '完美多頭',
                'description': '所有均線呈多頭排列，強勢上漲趨勢',
                'condition': 'MA5 > MA10 > MA20 > MA60 > MA120 > MA240',
                'count': len(stocks),
                'stocks': stocks
            }

        except Exception as e:
            logger.error(f"選出完美多頭股票失敗: {str(e)}")
            return {
                'name': '完美多頭',
                'description': '所有均線呈多頭排列，強勢上漲趨勢',
                'condition': 'MA5 > MA10 > MA20 > MA60 > MA120 > MA240',
                'count': 0,
                'stocks': [],
                'error': str(e)
            }

    def _select_short_bull(self, selection_date: date) -> Dict[str, Any]:
        """選出短線多頭股票

        短線多頭定義：MA5 > MA10 > MA20
        且收盤價 > MA5
        且不符合完美多頭條件（避免重複）

        Args:
            selection_date: 選股日期

        Returns:
            短線多頭股票列表
        """
        try:
            # 查詢符合條件的股票
            query = self.db.query(
                MovingAverages.stock_id,
                MovingAverages.ma_5,
                MovingAverages.ma_10,
                MovingAverages.ma_20,
                MovingAverages.ma_60,
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
                MovingAverages.trade_date == selection_date,
                # 短線多頭條件
                MovingAverages.ma_5 > MovingAverages.ma_10,
                MovingAverages.ma_10 > MovingAverages.ma_20,
                # 收盤價 > MA5
                StockDailyData.close_price > MovingAverages.ma_5,
                # 排除完美多頭（至少有一個條件不符合）
                or_(
                    MovingAverages.ma_20 <= MovingAverages.ma_60,
                    MovingAverages.ma_60 <= MovingAverages.ma_120,
                    MovingAverages.ma_120 <= MovingAverages.ma_240,
                    MovingAverages.ma_240.is_(None),
                    MovingAverages.ma_120.is_(None)
                )
            ).order_by(
                desc(StockDailyData.price_change)
            ).all()

            stocks = []
            for row in query:
                stocks.append({
                    'stock_code': row.stock_id,
                    'stock_name': row.stock_name,
                    'close_price': float(row.close_price),
                    'price_change': float(row.price_change) if row.price_change else 0,
                    'volume': int(row.volume),
                    'ma_5': float(row.ma_5),
                    'ma_10': float(row.ma_10),
                    'ma_20': float(row.ma_20),
                    'ma_60': float(row.ma_60) if row.ma_60 else None,
                    'ma_bias': round((float(row.close_price) - float(row.ma_5)) / float(row.ma_5) * 100, 2)  # 5日均線乖離率
                })

            return {
                'name': '短線多頭',
                'description': '短期均線呈多頭排列，短線上漲趨勢',
                'condition': 'MA5 > MA10 > MA20',
                'count': len(stocks),
                'stocks': stocks
            }

        except Exception as e:
            logger.error(f"選出短線多頭股票失敗: {str(e)}")
            return {
                'name': '短線多頭',
                'description': '短期均線呈多頭排列，短線上漲趨勢',
                'condition': 'MA5 > MA10 > MA20',
                'count': 0,
                'stocks': [],
                'error': str(e)
            }

    def _select_bear(self, selection_date: date) -> Dict[str, Any]:
        """選出空頭股票

        空頭定義：MA5 < MA10 < MA20 < MA60
        且收盤價 < MA5

        Args:
            selection_date: 選股日期

        Returns:
            空頭股票列表
        """
        try:
            # 查詢符合條件的股票
            query = self.db.query(
                MovingAverages.stock_id,
                MovingAverages.ma_5,
                MovingAverages.ma_10,
                MovingAverages.ma_20,
                MovingAverages.ma_60,
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
                MovingAverages.trade_date == selection_date,
                # 空頭條件
                MovingAverages.ma_5 < MovingAverages.ma_10,
                MovingAverages.ma_10 < MovingAverages.ma_20,
                MovingAverages.ma_20 < MovingAverages.ma_60,
                # 收盤價 < MA5
                StockDailyData.close_price < MovingAverages.ma_5,
                # 過濾掉均線資料不完整的股票
                MovingAverages.ma_60.isnot(None),
                MovingAverages.ma_60 > 0
            ).order_by(
                StockDailyData.price_change  # 空頭按跌幅排序
            ).all()

            stocks = []
            for row in query:
                stocks.append({
                    'stock_code': row.stock_id,
                    'stock_name': row.stock_name,
                    'close_price': float(row.close_price),
                    'price_change': float(row.price_change) if row.price_change else 0,
                    'volume': int(row.volume),
                    'ma_5': float(row.ma_5),
                    'ma_10': float(row.ma_10),
                    'ma_20': float(row.ma_20),
                    'ma_60': float(row.ma_60),
                    'ma_bias': round((float(row.close_price) - float(row.ma_5)) / float(row.ma_5) * 100, 2)  # 5日均線乖離率
                })

            return {
                'name': '空頭趨勢',
                'description': '均線呈空頭排列，下跌趨勢明顯',
                'condition': 'MA5 < MA10 < MA20 < MA60',
                'count': len(stocks),
                'stocks': stocks
            }

        except Exception as e:
            logger.error(f"選出空頭股票失敗: {str(e)}")
            return {
                'name': '空頭趨勢',
                'description': '均線呈空頭排列，下跌趨勢明顯',
                'condition': 'MA5 < MA10 < MA20 < MA60',
                'count': 0,
                'stocks': [],
                'error': str(e)
            }

    def _calculate_summary(self, strategies: Dict[str, Dict]) -> Dict[str, Any]:
        """計算選股結果總結

        Args:
            strategies: 各策略選股結果

        Returns:
            總結統計資訊
        """
        total_stocks = 0
        strategy_counts = {}

        for strategy_key, strategy_result in strategies.items():
            count = strategy_result.get('count', 0)
            total_stocks += count
            strategy_counts[strategy_key] = count

        # 取得所有有均線資料的股票總數
        total_stocks_with_ma = self.db.query(
            func.count(func.distinct(MovingAverages.stock_id))
        ).scalar() or 0

        return {
            'total_selected': total_stocks,
            'total_stocks_with_ma': total_stocks_with_ma,
            'selection_rate': round((total_stocks / total_stocks_with_ma * 100), 2) if total_stocks_with_ma > 0 else 0,
            'strategy_counts': strategy_counts
        }