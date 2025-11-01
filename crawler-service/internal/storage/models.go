package storage

import (
	"time"
)

// StockDailyData represents the stock_daily_data table structure
// 股票日線資料模型 - 與 Python SQLAlchemy 模型完全對應
type StockDailyData struct {
	ID               int64      `db:"id" json:"id"`
	StockCode        string     `db:"stock_code" json:"stock_code"`
	TradeDate        time.Time  `db:"trade_date" json:"trade_date"`
	OpenPrice        *float64   `db:"open_price" json:"open_price,omitempty"`
	HighPrice        *float64   `db:"high_price" json:"high_price,omitempty"`
	LowPrice         *float64   `db:"low_price" json:"low_price,omitempty"`
	ClosePrice       *float64   `db:"close_price" json:"close_price,omitempty"`
	Volume           *int64     `db:"volume" json:"volume,omitempty"`
	Turnover         *float64   `db:"turnover" json:"turnover,omitempty"`
	PriceChange      *float64   `db:"price_change" json:"price_change,omitempty"`
	PriceChangeRate  *float64   `db:"price_change_rate" json:"price_change_rate,omitempty"`
	MA5              *float64   `db:"ma5" json:"ma5,omitempty"`
	MA10             *float64   `db:"ma10" json:"ma10,omitempty"`
	MA20             *float64   `db:"ma20" json:"ma20,omitempty"`
	DataSource       string     `db:"data_source" json:"data_source"`
	DataQuality      *string    `db:"data_quality" json:"data_quality,omitempty"`
	IsValidated      bool       `db:"is_validated" json:"is_validated"`
	CreatedAt        time.Time  `db:"created_at" json:"created_at"`
	UpdatedAt        *time.Time `db:"updated_at" json:"updated_at,omitempty"`
}

// Stock represents the stocks table structure
// 股票基本資訊模型
type Stock struct {
	ID               int64      `db:"id" json:"id"`
	StockCode        string     `db:"stock_code" json:"stock_code"`
	StockName        string     `db:"stock_name" json:"stock_name"`
	Market           string     `db:"market" json:"market"`
	Industry         *string    `db:"industry" json:"industry,omitempty"`
	CapitalStock     *int64     `db:"capital_stock" json:"capital_stock,omitempty"`
	CapitalUpdatedAt *time.Time `db:"capital_updated_at" json:"capital_updated_at,omitempty"`
	IsActive         bool       `db:"is_active" json:"is_active"`
	CreatedAt        time.Time  `db:"created_at" json:"created_at"`
	UpdatedAt        *time.Time `db:"updated_at" json:"updated_at,omitempty"`
}

// TaskExecutionLog represents the task_execution_logs table structure
// 任務執行紀錄模型
type TaskExecutionLog struct {
	ID              int64      `db:"id" json:"id"`
	TaskName        string     `db:"task_name" json:"task_name"`
	TaskType        string     `db:"task_type" json:"task_type"`
	Parameters      *string    `db:"parameters" json:"parameters,omitempty"`
	Status          string     `db:"status" json:"status"`
	StartTime       time.Time  `db:"start_time" json:"start_time"`
	EndTime         *time.Time `db:"end_time" json:"end_time,omitempty"`
	DurationSeconds *float64   `db:"duration_seconds" json:"duration_seconds,omitempty"`
	Progress        int        `db:"progress" json:"progress"`
	ProcessedCount  int        `db:"processed_count" json:"processed_count"`
	TotalCount      int        `db:"total_count" json:"total_count"`
	SuccessCount    int        `db:"success_count" json:"success_count"`
	ErrorCount      int        `db:"error_count" json:"error_count"`
	ResultSummary   *string    `db:"result_summary" json:"result_summary,omitempty"`
	ErrorMessage    *string    `db:"error_message" json:"error_message,omitempty"`
	CreatedBy       *string    `db:"created_by" json:"created_by,omitempty"`
}

// InsertData represents the minimal data structure for inserting daily data
// 用於插入的簡化資料結構
type InsertData struct {
	StockCode   string
	TradeDate   time.Time
	OpenPrice   float64
	HighPrice   float64
	LowPrice    float64
	ClosePrice  float64
	Volume      int64
	Turnover    float64
	DataSource  string
	DataQuality string
}

// TableName returns the table name for StockDailyData
func (StockDailyData) TableName() string {
	return "stock_daily_data"
}

// TableName returns the table name for Stock
func (Stock) TableName() string {
	return "stocks"
}

// TableName returns the table name for TaskExecutionLog
func (TaskExecutionLog) TableName() string {
	return "task_execution_logs"
}
