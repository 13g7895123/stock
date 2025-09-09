"""Initial database tables for stock analysis system

Revision ID: 001
Revises: 
Create Date: 2024-12-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Create stocks table - 股票基本資訊表
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='股票代號'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='股票名稱'),
        sa.Column('market', sa.String(length=10), nullable=False, comment='市場別(TSE/TPEx)'),
        sa.Column('industry', sa.String(length=100), nullable=True, comment='產業別'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否啟用'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stocks_id'), 'stocks', ['id'], unique=False)
    op.create_index(op.f('ix_stocks_symbol'), 'stocks', ['symbol'], unique=True)

    # Create stock_daily_data table - 股票日線資料表
    op.create_table(
        'stock_daily_data',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('stock_id', sa.String(length=10), nullable=False, comment='股票代號'),
        sa.Column('trade_date', sa.DateTime(timezone=True), nullable=False, comment='交易日期'),
        sa.Column('open_price', sa.Float(), nullable=False, comment='開盤價'),
        sa.Column('high_price', sa.Float(), nullable=False, comment='最高價'),
        sa.Column('low_price', sa.Float(), nullable=False, comment='最低價'),
        sa.Column('close_price', sa.Float(), nullable=False, comment='收盤價'),
        sa.Column('volume', sa.BigInteger(), nullable=False, comment='成交量'),
        sa.Column('adjusted_close', sa.Float(), nullable=False, comment='還原收盤價'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'trade_date', name='uq_stock_date')
    )
    op.create_index(op.f('ix_stock_daily_data_id'), 'stock_daily_data', ['id'], unique=False)
    op.create_index(op.f('ix_stock_daily_data_stock_id'), 'stock_daily_data', ['stock_id'], unique=False)
    op.create_index(op.f('ix_stock_daily_data_trade_date'), 'stock_daily_data', ['trade_date'], unique=False)
    op.create_index('idx_stock_date_desc', 'stock_daily_data', ['stock_id', 'trade_date'], unique=False)
    op.create_index('idx_trade_date', 'stock_daily_data', ['trade_date'], unique=False)

    # Create moving_averages table - 均線資料表
    op.create_table(
        'moving_averages',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('stock_id', sa.String(length=10), nullable=False, comment='股票代號'),
        sa.Column('trade_date', sa.DateTime(timezone=True), nullable=False, comment='交易日期'),
        sa.Column('ma_5', sa.Float(), nullable=True, comment='5日均線'),
        sa.Column('ma_10', sa.Float(), nullable=True, comment='10日均線'),
        sa.Column('ma_20', sa.Float(), nullable=True, comment='20日均線'),
        sa.Column('ma_60', sa.Float(), nullable=True, comment='60日均線'),
        sa.Column('ma_120', sa.Float(), nullable=True, comment='120日均線'),
        sa.Column('ma_240', sa.Float(), nullable=True, comment='240日均線'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'trade_date', name='uq_ma_stock_date')
    )
    op.create_index(op.f('ix_moving_averages_id'), 'moving_averages', ['id'], unique=False)
    op.create_index(op.f('ix_moving_averages_stock_id'), 'moving_averages', ['stock_id'], unique=False)
    op.create_index(op.f('ix_moving_averages_trade_date'), 'moving_averages', ['trade_date'], unique=False)
    op.create_index('idx_ma_stock_date', 'moving_averages', ['stock_id', 'trade_date'], unique=False)
    op.create_index('idx_ma_trade_date', 'moving_averages', ['trade_date'], unique=False)

    # Create technical_indicators table - 技術指標表
    op.create_table(
        'technical_indicators',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('stock_id', sa.String(length=10), nullable=False, comment='股票代號'),
        sa.Column('trade_date', sa.DateTime(timezone=True), nullable=False, comment='交易日期'),
        sa.Column('rsi_14', sa.Float(), nullable=True, comment='14日RSI'),
        sa.Column('macd', sa.Float(), nullable=True, comment='MACD'),
        sa.Column('macd_signal', sa.Float(), nullable=True, comment='MACD訊號線'),
        sa.Column('kd_k', sa.Float(), nullable=True, comment='KD指標K值'),
        sa.Column('kd_d', sa.Float(), nullable=True, comment='KD指標D值'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'trade_date', name='uq_ti_stock_date')
    )
    op.create_index(op.f('ix_technical_indicators_id'), 'technical_indicators', ['id'], unique=False)
    op.create_index(op.f('ix_technical_indicators_stock_id'), 'technical_indicators', ['stock_id'], unique=False)
    op.create_index(op.f('ix_technical_indicators_trade_date'), 'technical_indicators', ['trade_date'], unique=False)
    op.create_index('idx_ti_stock_date', 'technical_indicators', ['stock_id', 'trade_date'], unique=False)
    op.create_index('idx_ti_trade_date', 'technical_indicators', ['trade_date'], unique=False)

    # Create stock_scores table - 股票評分表
    op.create_table(
        'stock_scores',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('stock_id', sa.String(length=10), nullable=False, comment='股票代號'),
        sa.Column('score_date', sa.DateTime(timezone=True), nullable=False, comment='評分日期'),
        sa.Column('pattern_score', sa.Float(), nullable=False, comment='型態評分'),
        sa.Column('trend_score', sa.Float(), nullable=False, comment='趨勢評分'),
        sa.Column('volume_score', sa.Float(), nullable=False, comment='成交量評分'),
        sa.Column('total_score', sa.Float(), nullable=False, comment='總評分'),
        sa.Column('ranking', sa.Integer(), nullable=True, comment='排名'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'score_date', name='uq_score_stock_date')
    )
    op.create_index(op.f('ix_stock_scores_id'), 'stock_scores', ['id'], unique=False)
    op.create_index(op.f('ix_stock_scores_stock_id'), 'stock_scores', ['stock_id'], unique=False)
    op.create_index(op.f('ix_stock_scores_score_date'), 'stock_scores', ['score_date'], unique=False)
    op.create_index('idx_score_date_score', 'stock_scores', ['score_date', 'total_score'], unique=False)
    op.create_index('idx_score_date_ranking', 'stock_scores', ['score_date', 'ranking'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_score_date_ranking', table_name='stock_scores')
    op.drop_index('idx_score_date_score', table_name='stock_scores')
    op.drop_index(op.f('ix_stock_scores_score_date'), table_name='stock_scores')
    op.drop_index(op.f('ix_stock_scores_stock_id'), table_name='stock_scores')
    op.drop_index(op.f('ix_stock_scores_id'), table_name='stock_scores')
    op.drop_table('stock_scores')
    
    op.drop_index('idx_ti_trade_date', table_name='technical_indicators')
    op.drop_index('idx_ti_stock_date', table_name='technical_indicators')
    op.drop_index(op.f('ix_technical_indicators_trade_date'), table_name='technical_indicators')
    op.drop_index(op.f('ix_technical_indicators_stock_id'), table_name='technical_indicators')
    op.drop_index(op.f('ix_technical_indicators_id'), table_name='technical_indicators')
    op.drop_table('technical_indicators')
    
    op.drop_index('idx_ma_trade_date', table_name='moving_averages')
    op.drop_index('idx_ma_stock_date', table_name='moving_averages')
    op.drop_index(op.f('ix_moving_averages_trade_date'), table_name='moving_averages')
    op.drop_index(op.f('ix_moving_averages_stock_id'), table_name='moving_averages')
    op.drop_index(op.f('ix_moving_averages_id'), table_name='moving_averages')
    op.drop_table('moving_averages')
    
    op.drop_index('idx_trade_date', table_name='stock_daily_data')
    op.drop_index('idx_stock_date_desc', table_name='stock_daily_data')
    op.drop_index(op.f('ix_stock_daily_data_trade_date'), table_name='stock_daily_data')
    op.drop_index(op.f('ix_stock_daily_data_stock_id'), table_name='stock_daily_data')
    op.drop_index(op.f('ix_stock_daily_data_id'), table_name='stock_daily_data')
    op.drop_table('stock_daily_data')
    
    op.drop_index(op.f('ix_stocks_symbol'), table_name='stocks')
    op.drop_index(op.f('ix_stocks_id'), table_name='stocks')
    op.drop_table('stocks')