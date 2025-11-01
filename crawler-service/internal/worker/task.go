package worker

import (
	"context"
	"time"
)

// TaskStatus 任務狀態
type TaskStatus string

const (
	TaskStatusPending   TaskStatus = "pending"
	TaskStatusRunning   TaskStatus = "running"
	TaskStatusCompleted TaskStatus = "completed"
	TaskStatusFailed    TaskStatus = "failed"
)

// Task 任務介面
type Task interface {
	Execute(ctx context.Context) error
	GetID() string
	GetSymbol() string
}

// StockFetchTask 股票爬取任務
type StockFetchTask struct {
	ID        string
	Symbol    string
	Broker    string
	CreatedAt time.Time
	Status    TaskStatus
	Error     error
	Result    interface{}
}

// Execute 執行任務
func (t *StockFetchTask) Execute(ctx context.Context) error {
	// 任務執行邏輯由 Worker Pool 處理
	return nil
}

// GetID 獲取任務 ID
func (t *StockFetchTask) GetID() string {
	return t.ID
}

// GetSymbol 獲取股票代碼
func (t *StockFetchTask) GetSymbol() string {
	return t.Symbol
}

// TaskResult 任務結果
type TaskResult struct {
	TaskID      string
	Symbol      string
	Success     bool
	Error       error
	RecordCount int
	Duration    time.Duration
	CompletedAt time.Time
}
