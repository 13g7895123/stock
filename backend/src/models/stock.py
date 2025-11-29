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
    stock_code = Column(String(20), unique=True, nullable=False, index=True, comment="股票代號")
    stock_name = Column(String(255), nullable=False, comment="股票名稱")
    market = Column(String(10), nullable=False, comment="市場別(TSE/TPEx)")
    industry = Column(String(100), comment="產業別")
    capital_stock = Column(BigInteger, comment="實收資本額（股本）單位：元")
    capital_updated_at = Column(DateTime(timezone=True), comment="股本資料更新時間")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 向後相容的屬性
    @property
    def symbol(self):
        return self.stock_code
    
    @symbol.setter
    def symbol(self, value):
        self.stock_code = value
    
    @property
    def name(self):
        return self.stock_name
    
    @name.setter
    def name(self, value):
        self.stock_name = value
    
    def __repr__(self) -> str:
        return f"<Stock(stock_code='{self.stock_code}', stock_name='{self.stock_name}', market='{self.market}')>"


class StockDailyData(Base):
    """Stock daily price data model - 股票日線資料表."""
    
    __tablename__ = "stock_daily_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True, comment="股票代號")
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="交易日期")
    open_price = Column(Float, comment="開盤價")
    high_price = Column(Float, comment="最高價")
    low_price = Column(Float, comment="最低價")
    close_price = Column(Float, comment="收盤價")
    volume = Column(BigInteger, comment="成交量")
    turnover = Column(Float, comment="成交額")
    price_change = Column(Float, comment="價差")
    price_change_rate = Column(Float, comment="漲跌幅")
    ma5 = Column(Float, comment="5日均線")
    ma10 = Column(Float, comment="10日均線")
    ma20 = Column(Float, comment="20日均線")
    data_source = Column(String(50), nullable=False, comment="資料來源")
    data_quality = Column(String(20), comment="資料品質")
    is_validated = Column(Boolean, default=False, comment="是否已驗證")
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    
    # 為了向後相容，提供stock_id屬性
    @property 
    def stock_id(self):
        return self.stock_code
    
    @stock_id.setter
    def stock_id(self, value):
        self.stock_code = value
    
    # 為了向後相容，提供adjusted_close屬性
    @property
    def adjusted_close(self):
        return self.close_price
    
    @adjusted_close.setter  
    def adjusted_close(self, value):
        self.close_price = value
    
    def __repr__(self) -> str:
        return f"<StockDailyData(stock_code='{self.stock_code}', trade_date='{self.trade_date}', close={self.close_price})>"


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
    ma_72 = Column(Float, comment="72日均線")
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


class InstitutionalTradingData(Base):
    """Institutional trading data model - 投信外資買賣超資料表."""

    __tablename__ = "institutional_trading_data"

    id = Column(BigInteger, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True, comment="股票代號")
    stock_name = Column(String(255), nullable=False, comment="股票名稱")
    trade_date = Column(DateTime(timezone=True), nullable=False, index=True, comment="交易日期")

    # 外陸資 (不含外資自營商)
    foreign_buy = Column(BigInteger, default=0, comment="外陸資買進股數")
    foreign_sell = Column(BigInteger, default=0, comment="外陸資賣出股數")
    foreign_net = Column(BigInteger, default=0, comment="外陸資買賣超股數")

    # 外資自營商
    foreign_dealer_buy = Column(BigInteger, default=0, comment="外資自營商買進股數")
    foreign_dealer_sell = Column(BigInteger, default=0, comment="外資自營商賣出股數")
    foreign_dealer_net = Column(BigInteger, default=0, comment="外資自營商買賣超股數")

    # 投信
    investment_trust_buy = Column(BigInteger, default=0, comment="投信買進股數")
    investment_trust_sell = Column(BigInteger, default=0, comment="投信賣出股數")
    investment_trust_net = Column(BigInteger, default=0, comment="投信買賣超股數")

    # 自營商
    dealer_net = Column(BigInteger, default=0, comment="自營商買賣超股數")
    dealer_self_buy = Column(BigInteger, default=0, comment="自營商買進股數(自行買賣)")
    dealer_self_sell = Column(BigInteger, default=0, comment="自營商賣出股數(自行買賣)")
    dealer_self_net = Column(BigInteger, default=0, comment="自營商買賣超股數(自行買賣)")
    dealer_hedge_buy = Column(BigInteger, default=0, comment="自營商買進股數(避險)")
    dealer_hedge_sell = Column(BigInteger, default=0, comment="自營商賣出股數(避險)")
    dealer_hedge_net = Column(BigInteger, default=0, comment="自營商買賣超股數(避險)")

    # 三大法人合計
    total_institutional_net = Column(BigInteger, default=0, comment="三大法人買賣超股數")

    # 資料來源和品質
    data_source = Column(String(50), default="TWSE_T86", comment="資料來源")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="建立時間")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新時間")

    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_institutional_stock_date'),
        Index('idx_institutional_stock_date', 'stock_code', 'trade_date'),
        Index('idx_institutional_trade_date', 'trade_date'),
        Index('idx_institutional_stock_code', 'stock_code'),
    )

    def __repr__(self) -> str:
        return f"<InstitutionalTradingData(stock_code='{self.stock_code}', trade_date='{self.trade_date}', total_net={self.total_institutional_net})>"


class TaskExecutionLog(Base):
    """Task execution log model - 任務執行紀錄表."""

    __tablename__ = "task_execution_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False, index=True, comment="任務名稱")
    task_type = Column(String(50), nullable=False, comment="任務類型")
    parameters = Column(String, comment="執行參數(JSON格式)")
    status = Column(String(20), nullable=False, default="running", comment="執行狀態: running, completed, failed, cancelled")
    start_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="開始時間")
    end_time = Column(DateTime(timezone=True), comment="結束時間")
    duration_seconds = Column(Float, comment="執行時長(秒)")
    progress = Column(Integer, default=0, comment="執行進度(0-100)")
    processed_count = Column(Integer, default=0, comment="已處理數量")
    total_count = Column(Integer, default=0, comment="總數量")
    success_count = Column(Integer, default=0, comment="成功數量")
    error_count = Column(Integer, default=0, comment="錯誤數量")
    result_summary = Column(String, comment="執行結果摘要")
    error_message = Column(String, comment="錯誤訊息")
    created_by = Column(String(50), comment="執行者")
    
    __table_args__ = (
        Index('idx_task_start_time', 'start_time'),
        Index('idx_task_status', 'status'),
        Index('idx_task_type_time', 'task_type', 'start_time'),
    )
    
    def __repr__(self) -> str:
        return f"<TaskExecutionLog(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"