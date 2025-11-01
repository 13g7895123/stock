package scraper

import (
	"context"
	"time"
)

// DailyData 股票日線資料
type DailyData struct {
	StockCode   string    `json:"stock_code"`
	TradeDate   time.Time `json:"trade_date"`
	OpenPrice   float64   `json:"open_price"`
	HighPrice   float64   `json:"high_price"`
	LowPrice    float64   `json:"low_price"`
	ClosePrice  float64   `json:"close_price"`
	Volume      int64     `json:"volume"`
	Turnover    float64   `json:"turnover,omitempty"`
	DataSource  string    `json:"data_source"`
	DataQuality string    `json:"data_quality"`
}

// Broker 券商介面
type Broker interface {
	// FetchDailyData 獲取股票日線資料
	FetchDailyData(ctx context.Context, symbol string) ([]DailyData, error)

	// Name 券商名稱
	Name() string

	// HealthCheck 健康檢查
	HealthCheck(ctx context.Context) error
}

// FetchResult 爬取結果
type FetchResult struct {
	Symbol     string
	Data       []DailyData
	Source     string
	Success    bool
	Error      error
	Duration   time.Duration
	RecordCount int
}

// BatchResult 批次處理結果
type BatchResult struct {
	TotalProcessed int
	SuccessCount   int
	ErrorCount     int
	SkippedCount   int
	Duration       time.Duration
	Errors         []BatchError
}

// BatchError 批次錯誤
type BatchError struct {
	Symbol  string
	Source  string
	Error   string
	Time    time.Time
}
