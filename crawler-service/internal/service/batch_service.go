package service

import (
	"context"
	"fmt"
	"time"

	"github.com/stock-analysis/crawler-service/internal/worker"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// BatchService 批次處理服務
type BatchService struct {
	workerPool *worker.WorkerPool
}

// NewBatchService 創建批次服務
func NewBatchService(workerPool *worker.WorkerPool) *BatchService {
	return &BatchService{
		workerPool: workerPool,
	}
}

// BatchUpdateRequest 批次更新請求
type BatchUpdateRequest struct {
	Symbols []string `json:"symbols"`
	Broker  string   `json:"broker,omitempty"`
}

// BatchUpdateResponse 批次更新響應
type BatchUpdateResponse struct {
	BatchID      string    `json:"batch_id"`
	TotalSymbols int       `json:"total_symbols"`
	StartedAt    time.Time `json:"started_at"`
	Status       string    `json:"status"`
	Message      string    `json:"message"`
}

// BatchStatusResponse 批次狀態響應
type BatchStatusResponse struct{
	BatchID        string                 `json:"batch_id"`
	TotalTasks     int                    `json:"total_tasks"`
	PendingTasks   int                    `json:"pending_tasks"`
	RunningTasks   int                    `json:"running_tasks"`
	CompletedTasks int                    `json:"completed_tasks"`
	FailedTasks    int                    `json:"failed_tasks"`
	Tasks          []TaskStatusInfo       `json:"tasks"`
	Stats          map[string]interface{} `json:"stats"`
}

// TaskStatusInfo 任務狀態資訊
type TaskStatusInfo struct {
	TaskID      string `json:"task_id"`
	Symbol      string `json:"symbol"`
	Status      string `json:"status"`
	RecordCount int    `json:"record_count,omitempty"`
	Error       string `json:"error,omitempty"`
}

// BatchUpdateStocks 批次更新股票
func (s *BatchService) BatchUpdateStocks(ctx context.Context, req *BatchUpdateRequest) (*BatchUpdateResponse, error) {
	if len(req.Symbols) == 0 {
		return nil, fmt.Errorf("no symbols provided")
	}

	logger.Info("Starting batch update",
		zap.Int("symbol_count", len(req.Symbols)),
		zap.String("broker", req.Broker),
	)

	batchID := fmt.Sprintf("batch_%d", time.Now().Unix())
	startTime := time.Now()

	// 提交所有任務到 Worker Pool
	successCount := 0
	for i, symbol := range req.Symbols {
		task := &worker.StockFetchTask{
			ID:        fmt.Sprintf("%s_task_%d", batchID, i),
			Symbol:    symbol,
			Broker:    req.Broker,
			CreatedAt: time.Now(),
			Status:    worker.TaskStatusPending,
		}

		err := s.workerPool.Submit(task)
		if err != nil {
			logger.Error("Failed to submit task",
				zap.String("symbol", symbol),
				zap.Error(err),
			)
			continue
		}
		successCount++
	}

	response := &BatchUpdateResponse{
		BatchID:      batchID,
		TotalSymbols: successCount,
		StartedAt:    startTime,
		Status:       "processing",
		Message:      fmt.Sprintf("Submitted %d tasks successfully", successCount),
	}

	logger.Info("Batch update started",
		zap.String("batch_id", batchID),
		zap.Int("submitted_tasks", successCount),
	)

	return response, nil
}

// GetBatchStatus 獲取批次狀態
func (s *BatchService) GetBatchStatus(ctx context.Context, batchID string) (*BatchStatusResponse, error) {
	// 獲取所有任務
	allTasks := s.workerPool.GetAllTasks()

	// 過濾屬於該批次的任務
	batchTasks := []*worker.StockFetchTask{}
	for _, task := range allTasks {
		// 檢查任務 ID 是否屬於該批次
		if len(task.ID) > len(batchID) && task.ID[:len(batchID)] == batchID {
			batchTasks = append(batchTasks, task)
		}
	}

	if len(batchTasks) == 0 {
		return nil, fmt.Errorf("batch not found: %s", batchID)
	}

	// 統計各狀態任務數量
	pending := 0
	running := 0
	completed := 0
	failed := 0

	taskInfos := make([]TaskStatusInfo, len(batchTasks))
	for i, task := range batchTasks {
		switch task.Status {
		case worker.TaskStatusPending:
			pending++
		case worker.TaskStatusRunning:
			running++
		case worker.TaskStatusCompleted:
			completed++
		case worker.TaskStatusFailed:
			failed++
		}

		taskInfo := TaskStatusInfo{
			TaskID: task.ID,
			Symbol: task.Symbol,
			Status: string(task.Status),
		}

		if task.Result != nil {
			if result, ok := task.Result.(*FetchStockDailyResponse); ok {
				taskInfo.RecordCount = result.RecordCount
			}
		}

		if task.Error != nil {
			taskInfo.Error = task.Error.Error()
		}

		taskInfos[i] = taskInfo
	}

	// 獲取 Worker Pool 統計
	stats := s.workerPool.Stats()

	response := &BatchStatusResponse{
		BatchID:        batchID,
		TotalTasks:     len(batchTasks),
		PendingTasks:   pending,
		RunningTasks:   running,
		CompletedTasks: completed,
		FailedTasks:    failed,
		Tasks:          taskInfos,
		Stats:          stats,
	}

	return response, nil
}

// GetWorkerPoolStats 獲取 Worker Pool 統計
func (s *BatchService) GetWorkerPoolStats() map[string]interface{} {
	return s.workerPool.Stats()
}
