"""Add institutional_trading_data table

Revision ID: 003
Revises: 30fff3dcd91b
Create Date: 2025-09-24 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "30fff3dcd91b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create institutional_trading_data table
    op.create_table(
        "institutional_trading_data",
        sa.Column("id", sa.BigInteger(), nullable=False, primary_key=True, index=True),
        sa.Column("stock_code", sa.String(10), nullable=False, index=True, comment="股票代號"),
        sa.Column("stock_name", sa.String(255), nullable=False, comment="股票名稱"),
        sa.Column("trade_date", sa.DateTime(timezone=True), nullable=False, index=True, comment="交易日期"),

        # 外陸資 (不含外資自營商)
        sa.Column("foreign_buy", sa.BigInteger(), default=0, comment="外陸資買進股數"),
        sa.Column("foreign_sell", sa.BigInteger(), default=0, comment="外陸資賣出股數"),
        sa.Column("foreign_net", sa.BigInteger(), default=0, comment="外陸資買賣超股數"),

        # 外資自營商
        sa.Column("foreign_dealer_buy", sa.BigInteger(), default=0, comment="外資自營商買進股數"),
        sa.Column("foreign_dealer_sell", sa.BigInteger(), default=0, comment="外資自營商賣出股數"),
        sa.Column("foreign_dealer_net", sa.BigInteger(), default=0, comment="外資自營商買賣超股數"),

        # 投信
        sa.Column("investment_trust_buy", sa.BigInteger(), default=0, comment="投信買進股數"),
        sa.Column("investment_trust_sell", sa.BigInteger(), default=0, comment="投信賣出股數"),
        sa.Column("investment_trust_net", sa.BigInteger(), default=0, comment="投信買賣超股數"),

        # 自營商
        sa.Column("dealer_net", sa.BigInteger(), default=0, comment="自營商買賣超股數"),
        sa.Column("dealer_self_buy", sa.BigInteger(), default=0, comment="自營商買進股數(自行買賣)"),
        sa.Column("dealer_self_sell", sa.BigInteger(), default=0, comment="自營商賣出股數(自行買賣)"),
        sa.Column("dealer_self_net", sa.BigInteger(), default=0, comment="自營商買賣超股數(自行買賣)"),
        sa.Column("dealer_hedge_buy", sa.BigInteger(), default=0, comment="自營商買進股數(避險)"),
        sa.Column("dealer_hedge_sell", sa.BigInteger(), default=0, comment="自營商賣出股數(避險)"),
        sa.Column("dealer_hedge_net", sa.BigInteger(), default=0, comment="自營商買賣超股數(避險)"),

        # 三大法人合計
        sa.Column("total_institutional_net", sa.BigInteger(), default=0, comment="三大法人買賣超股數"),

        # 資料來源和品質
        sa.Column("data_source", sa.String(50), default="TWSE_T86", comment="資料來源"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now(), comment="建立時間"),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=func.now(), comment="更新時間"),
    )

    # Create unique constraint
    op.create_unique_constraint(
        'uq_institutional_stock_date',
        'institutional_trading_data',
        ['stock_code', 'trade_date']
    )

    # Create indexes
    op.create_index(
        'idx_institutional_stock_date',
        'institutional_trading_data',
        ['stock_code', 'trade_date']
    )

    op.create_index(
        'idx_institutional_trade_date',
        'institutional_trading_data',
        ['trade_date']
    )

    op.create_index(
        'idx_institutional_stock_code',
        'institutional_trading_data',
        ['stock_code']
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index('idx_institutional_stock_code', 'institutional_trading_data')
    op.drop_index('idx_institutional_trade_date', 'institutional_trading_data')
    op.drop_index('idx_institutional_stock_date', 'institutional_trading_data')

    # Drop unique constraint
    op.drop_constraint('uq_institutional_stock_date', 'institutional_trading_data', type_='unique')

    # Drop table
    op.drop_table('institutional_trading_data')