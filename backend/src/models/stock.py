"""Stock data models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Index, UniqueConstraint, Boolean, BigInteger
from sqlalchemy.sql import func

from src.core.database import Base


class Stock(Base):
    """Stock basic information model - 股票基本資訊表."""
    
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment="股票代號")
    name = Column(String(255), nullable=False, comment="股票名稱")
    market = Column(String(10), nullable=False, comment="市場別(TSE/TPEx)")
    industry = Column(String(100), comment="產業別")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Stock(symbol='{self.symbol}', name='{self.name}', market='{self.market}')>"


class StockDailyData(Base):
    """Stock daily price data model - 股票日線資料表."""
    
    __tablename__ = "stock_daily_data"
    
    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True, comment="股票代號")
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="交易日期")
    open_price = Column(Float, nullable=False, comment="開盤價")
    high_price = Column(Float, nullable=False, comment="最高價")
    low_price = Column(Float, nullable=False, comment="最低價")
    close_price = Column(Float, nullable=False, comment="收盤價")
    volume = Column(BigInteger, nullable=False, comment="成交量")
    adjusted_close = Column(Float, nullable=False, comment="還原收盤價")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Create unique constraint and indexes for performance
    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_stock_date'),
        Index('idx_stock_date_desc', 'stock_id', 'trade_date'),
        Index('idx_trade_date', 'trade_date'),
    )
    
    def __repr__(self) -> str:
        return f"<StockDailyData(stock_id='{self.stock_id}', trade_date='{self.trade_date}', close={self.close_price})>"


class MovingAverages(Base):
    """Moving averages data model - 均線資料表."""
    
    __tablename__ = "moving_averages"
    
    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True, comment="股票代號")
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="交易日期")
    ma_5 = Column(Float, comment="5日均線")
    ma_10 = Column(Float, comment="10日均線") 
    ma_20 = Column(Float, comment="20日均線")
    ma_60 = Column(Float, comment="60日均線")
    ma_120 = Column(Float, comment="120日均線")
    ma_240 = Column(Float, comment="240日均線")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_ma_stock_date'),
        Index('idx_ma_stock_date', 'stock_id', 'trade_date'),
        Index('idx_ma_trade_date', 'trade_date'),
    )
    
    def __repr__(self) -> str:
        return f"<MovingAverages(stock_id='{self.stock_id}', trade_date='{self.trade_date}', ma_20={self.ma_20})>"


class TechnicalIndicators(Base):
    """Technical indicators data model - 技術指標表."""
    
    __tablename__ = "technical_indicators"
    
    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True, comment="股票代號")
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="交易日期")
    rsi_14 = Column(Float, comment="14日RSI")
    macd = Column(Float, comment="MACD")
    macd_signal = Column(Float, comment="MACD訊號線")
    kd_k = Column(Float, comment="KD指標K值")
    kd_d = Column(Float, comment="KD指標D值")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_ti_stock_date'),
        Index('idx_ti_stock_date', 'stock_id', 'trade_date'),
        Index('idx_ti_trade_date', 'trade_date'),
    )
    
    def __repr__(self) -> str:
        return f"<TechnicalIndicators(stock_id='{self.stock_id}', trade_date='{self.trade_date}', rsi={self.rsi_14})>"


class StockScores(Base):
    """Stock scoring data model - 股票評分表."""
    
    __tablename__ = "stock_scores"
    
    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True, comment="股票代號")
    score_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="評分日期")
    pattern_score = Column(Float, nullable=False, comment="型態評分")
    trend_score = Column(Float, nullable=False, comment="趨勢評分")
    volume_score = Column(Float, nullable=False, comment="成交量評分")
    total_score = Column(Float, nullable=False, comment="總評分")
    ranking = Column(Integer, comment="排名")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'score_date', name='uq_score_stock_date'),
        Index('idx_score_date_score', 'score_date', 'total_score'),
        Index('idx_score_date_ranking', 'score_date', 'ranking'),
    )
    
    def __repr__(self) -> str:
        return f"<StockScores(stock_id='{self.stock_id}', score_date='{self.score_date}', total_score={self.total_score})>"