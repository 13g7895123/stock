"""Service for fetching and updating stock capital data."""

import csv
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.stock import Stock

logger = logging.getLogger(__name__)


class CapitalStockService:
    """Service for managing stock capital data."""

    # 政府開放資料平台的 CSV URLs
    TSE_CAPITAL_URL = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"  # 上市公司
    OTC_CAPITAL_URL = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"  # 上櫃公司

    def __init__(self, db: Session = None):
        """Initialize the service."""
        self.db = db or next(get_db())

    async def fetch_listed_company_capital(self) -> List[Dict]:
        """
        Fetch capital data for listed companies (上市公司).

        Returns:
            List of dictionaries containing company capital data
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(self.TSE_CAPITAL_URL)
                response.raise_for_status()

                # 解碼 CSV 內容（使用 UTF-8 或 BIG5）
                try:
                    content = response.text
                except UnicodeDecodeError:
                    content = response.content.decode('big5')

                # 解析 CSV
                csv_reader = csv.DictReader(io.StringIO(content))
                data = []

                for row in csv_reader:
                    # 提取重要欄位
                    company_data = {
                        'stock_code': row.get('公司代號', '').strip(),
                        'company_name': row.get('公司名稱', '').strip(),
                        'capital_stock': self._parse_capital(row.get('實收資本額', '0')),
                        'industry': row.get('產業別', '').strip(),
                        'market': 'TSE'
                    }
                    if company_data['stock_code']:
                        data.append(company_data)

                logger.info(f"Successfully fetched {len(data)} listed companies capital data")
                return data

        except Exception as e:
            logger.error(f"Error fetching listed company capital data: {e}")
            raise

    async def fetch_otc_company_capital(self) -> List[Dict]:
        """
        Fetch capital data for OTC companies (上櫃公司).

        Returns:
            List of dictionaries containing company capital data
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(self.OTC_CAPITAL_URL)
                response.raise_for_status()

                # 解碼 CSV 內容
                try:
                    content = response.text
                except UnicodeDecodeError:
                    content = response.content.decode('big5')

                # 解析 CSV
                csv_reader = csv.DictReader(io.StringIO(content))
                data = []

                for row in csv_reader:
                    # 提取重要欄位
                    company_data = {
                        'stock_code': row.get('公司代號', '').strip(),
                        'company_name': row.get('公司名稱', '').strip(),
                        'capital_stock': self._parse_capital(row.get('實收資本額', '0')),
                        'industry': row.get('產業別', '').strip(),
                        'market': 'TPEx'
                    }
                    if company_data['stock_code']:
                        data.append(company_data)

                logger.info(f"Successfully fetched {len(data)} OTC companies capital data")
                return data

        except Exception as e:
            logger.error(f"Error fetching OTC company capital data: {e}")
            raise

    def _parse_capital(self, capital_str: str) -> int:
        """
        Parse capital string to integer (in NTD).

        Args:
            capital_str: Capital string from CSV

        Returns:
            Capital amount in NTD (integer)
        """
        try:
            # 移除逗號和空格
            capital_str = capital_str.replace(',', '').replace(' ', '').strip()

            # 如果是空字串或無效值，返回 0
            if not capital_str or capital_str == '-' or capital_str == 'N/A':
                return 0

            # 轉換為整數
            return int(float(capital_str))

        except (ValueError, TypeError):
            logger.warning(f"Could not parse capital value: {capital_str}")
            return 0

    async def update_all_capital_stock(self) -> Dict:
        """
        Update capital stock data for all companies.

        Returns:
            Dictionary with update statistics
        """
        try:
            # 獲取上市和上櫃公司資料
            listed_data = await self.fetch_listed_company_capital()
            otc_data = await self.fetch_otc_company_capital()

            # 合併資料
            all_data = listed_data + otc_data

            # 統計資訊
            stats = {
                'total_fetched': len(all_data),
                'updated_count': 0,
                'new_count': 0,
                'error_count': 0,
                'listed_count': len(listed_data),
                'otc_count': len(otc_data)
            }

            # 更新資料庫
            update_time = datetime.now()

            for company in all_data:
                try:
                    # 查詢現有股票
                    stock = self.db.query(Stock).filter(
                        Stock.stock_code == company['stock_code']
                    ).first()

                    if stock:
                        # 更新現有股票的股本資料
                        stock.capital_stock = company['capital_stock']
                        stock.capital_updated_at = update_time
                        if company.get('industry'):
                            stock.industry = company['industry']
                        stats['updated_count'] += 1
                    else:
                        # 建立新股票（如果資料庫中沒有）
                        stock = Stock(
                            stock_code=company['stock_code'],
                            stock_name=company['company_name'],
                            market=company['market'],
                            industry=company.get('industry'),
                            capital_stock=company['capital_stock'],
                            capital_updated_at=update_time,
                            is_active=True
                        )
                        self.db.add(stock)
                        stats['new_count'] += 1

                except Exception as e:
                    logger.error(f"Error updating stock {company.get('stock_code')}: {e}")
                    stats['error_count'] += 1
                    continue

            # 提交變更
            self.db.commit()

            logger.info(
                f"Capital stock update completed - "
                f"Updated: {stats['updated_count']}, "
                f"New: {stats['new_count']}, "
                f"Errors: {stats['error_count']}"
            )

            return stats

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in update_all_capital_stock: {e}")
            raise

    def get_capital_statistics(self) -> Dict:
        """
        Get statistics about capital stock data.

        Returns:
            Dictionary containing statistics
        """
        try:
            # 總股票數
            total_stocks = self.db.query(Stock).count()

            # 有股本資料的股票數
            stocks_with_capital = self.db.query(Stock).filter(
                Stock.capital_stock.isnot(None),
                Stock.capital_stock > 0
            ).count()

            # 按市場統計
            tse_with_capital = self.db.query(Stock).filter(
                Stock.market == 'TSE',
                Stock.capital_stock.isnot(None),
                Stock.capital_stock > 0
            ).count()

            otc_with_capital = self.db.query(Stock).filter(
                Stock.market == 'TPEx',
                Stock.capital_stock.isnot(None),
                Stock.capital_stock > 0
            ).count()

            # 最後更新時間
            last_update = self.db.query(Stock.capital_updated_at).filter(
                Stock.capital_updated_at.isnot(None)
            ).order_by(Stock.capital_updated_at.desc()).first()

            # 股本分布統計
            large_cap = self.db.query(Stock).filter(
                Stock.capital_stock >= 10000000000  # >= 100億
            ).count()

            mid_cap = self.db.query(Stock).filter(
                Stock.capital_stock >= 1000000000,  # >= 10億
                Stock.capital_stock < 10000000000   # < 100億
            ).count()

            small_cap = self.db.query(Stock).filter(
                Stock.capital_stock > 0,
                Stock.capital_stock < 1000000000  # < 10億
            ).count()

            return {
                'total_stocks': total_stocks,
                'stocks_with_capital': stocks_with_capital,
                'stocks_without_capital': total_stocks - stocks_with_capital,
                'completeness_rate': round(stocks_with_capital / total_stocks * 100, 2) if total_stocks > 0 else 0,
                'tse_with_capital': tse_with_capital,
                'otc_with_capital': otc_with_capital,
                'last_update': last_update[0].isoformat() if last_update and last_update[0] else None,
                'capital_distribution': {
                    'large_cap': large_cap,  # >= 100億
                    'mid_cap': mid_cap,      # 10億-100億
                    'small_cap': small_cap   # < 10億
                }
            }

        except Exception as e:
            logger.error(f"Error getting capital statistics: {e}")
            raise

    def get_stock_capital(self, stock_code: str) -> Optional[Dict]:
        """
        Get capital data for a specific stock.

        Args:
            stock_code: Stock code

        Returns:
            Dictionary with stock capital data or None
        """
        try:
            stock = self.db.query(Stock).filter(
                Stock.stock_code == stock_code
            ).first()

            if not stock:
                return None

            return {
                'stock_code': stock.stock_code,
                'stock_name': stock.stock_name,
                'market': stock.market,
                'industry': stock.industry,
                'capital_stock': stock.capital_stock,
                'capital_stock_billion': round(stock.capital_stock / 1000000000, 2) if stock.capital_stock else 0,
                'capital_updated_at': stock.capital_updated_at.isoformat() if stock.capital_updated_at else None,
                'capital_category': self._get_capital_category(stock.capital_stock)
            }

        except Exception as e:
            logger.error(f"Error getting capital for stock {stock_code}: {e}")
            raise

    def _get_capital_category(self, capital: Optional[int]) -> str:
        """
        Categorize stock based on capital size.

        Args:
            capital: Capital amount in NTD

        Returns:
            Category string
        """
        if not capital or capital == 0:
            return '無資料'
        elif capital >= 10000000000:  # >= 100億
            return '大型股'
        elif capital >= 1000000000:   # >= 10億
            return '中型股'
        else:
            return '小型股'