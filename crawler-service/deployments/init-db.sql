-- 資料庫初始化腳本
-- 確保必要的表和索引存在

-- 檢查並建立 stock_daily_data 表（如果不存在）
CREATE TABLE IF NOT EXISTS stock_daily_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    turnover DECIMAL(15, 2),
    data_source VARCHAR(50),
    data_quality VARCHAR(20),
    is_validated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

-- 建立索引
CREATE INDEX IF NOT EXISTS idx_stock_daily_code ON stock_daily_data(stock_code);
CREATE INDEX IF NOT EXISTS idx_stock_daily_date ON stock_daily_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_stock_daily_code_date ON stock_daily_data(stock_code, trade_date DESC);

-- 建立更新時間觸發器函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 建立觸發器
DROP TRIGGER IF EXISTS update_stock_daily_data_updated_at ON stock_daily_data;
CREATE TRIGGER update_stock_daily_data_updated_at
    BEFORE UPDATE ON stock_daily_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入測試資料（選配）
-- INSERT INTO stock_daily_data (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, data_source, data_quality)
-- VALUES ('2330', '2024-01-01', 100.0, 105.0, 99.0, 103.0, 10000000, 'go_broker_crawler', 'corrected_daily')
-- ON CONFLICT (stock_code, trade_date) DO NOTHING;

-- 顯示表資訊
SELECT 'Database initialization completed' AS status;
SELECT count(*) AS stock_daily_data_count FROM stock_daily_data;
