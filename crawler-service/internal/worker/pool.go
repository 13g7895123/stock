package worker

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StockFetcher 股票爬取介面（避免循環依賴）
type StockFetcher interface {
	FetchStockDaily(ctx context.Context, symbol string, broker string) (interface{}, error)
}

// WorkerPool Worker 池
type WorkerPool struct {
	workers      int
	taskQueue    chan *StockFetchTask
	resultQueue  chan *TaskResult
	stockFetcher StockFetcher
	wg           sync.WaitGroup
	ctx          context.Context
	cancel       context.CancelFunc
	mu           sync.RWMutex
	tasks        map[string]*StockFetchTask
}

// NewWorkerPool 創建 Worker Pool
func NewWorkerPool(workers int, stockFetcher StockFetcher) *WorkerPool {
	ctx, cancel := context.WithCancel(context.Background())

	return &WorkerPool{
		workers:      workers,
		taskQueue:    make(chan *StockFetchTask, workers*2),
		resultQueue:  make(chan *TaskResult, workers*2),
		stockFetcher: stockFetcher,
		ctx:          ctx,
		cancel:       cancel,
		tasks:        make(map[string]*StockFetchTask),
	}
}

// Start 啟動 Worker Pool
func (p *WorkerPool) Start() {
	logger.Info("Starting worker pool",
		zap.Int("workers", p.workers),
	)

	for i := 0; i < p.workers; i++ {
		p.wg.Add(1)
		go p.worker(i)
	}

	// 啟動結果處理器
	go p.resultProcessor()
}

// worker Worker goroutine
func (p *WorkerPool) worker(id int) {
	defer p.wg.Done()

	logger.Info("Worker started",
		zap.Int("worker_id", id),
	)

	for {
		select {
		case <-p.ctx.Done():
			logger.Info("Worker stopped",
				zap.Int("worker_id", id),
			)
			return

		case task := <-p.taskQueue:
			if task == nil {
				continue
			}

			logger.Info("Worker processing task",
				zap.Int("worker_id", id),
				zap.String("task_id", task.ID),
				zap.String("symbol", task.Symbol),
			)

			// 更新任務狀態
			p.updateTaskStatus(task.ID, TaskStatusRunning)

			// 執行任務
			result := p.executeTask(task)

			// 發送結果
			select {
			case p.resultQueue <- result:
			case <-p.ctx.Done():
				return
			}
		}
	}
}

// executeTask 執行任務
func (p *WorkerPool) executeTask(task *StockFetchTask) *TaskResult {
	startTime := time.Now()

	// 創建任務上下文（帶超時）
	ctx, cancel := context.WithTimeout(p.ctx, 2*time.Minute)
	defer cancel()

	// 調用服務層爬取資料
	response, err := p.stockFetcher.FetchStockDaily(ctx, task.Symbol, task.Broker)

	duration := time.Since(startTime)

	result := &TaskResult{
		TaskID:      task.ID,
		Symbol:      task.Symbol,
		Success:     err == nil,
		Error:       err,
		Duration:    duration,
		CompletedAt: time.Now(),
	}

	if response != nil {
		task.Result = response
		// 嘗試提取記錄數
		if respData, ok := response.(map[string]interface{}); ok {
			if count, exists := respData["record_count"]; exists {
				if c, ok := count.(int); ok {
					result.RecordCount = c
				}
			}
		}
	}

	return result
}

// resultProcessor 結果處理器
func (p *WorkerPool) resultProcessor() {
	for {
		select {
		case <-p.ctx.Done():
			return

		case result := <-p.resultQueue:
			if result == nil {
				continue
			}

			// 更新任務狀態
			if result.Success {
				p.updateTaskStatus(result.TaskID, TaskStatusCompleted)
				logger.Info("Task completed successfully",
					zap.String("task_id", result.TaskID),
					zap.String("symbol", result.Symbol),
					zap.Int("records", result.RecordCount),
					zap.Duration("duration", result.Duration),
				)
			} else {
				p.updateTaskStatus(result.TaskID, TaskStatusFailed)
				p.updateTaskError(result.TaskID, result.Error)
				logger.Error("Task failed",
					zap.String("task_id", result.TaskID),
					zap.String("symbol", result.Symbol),
					zap.Error(result.Error),
				)
			}
		}
	}
}

// Submit 提交任務
func (p *WorkerPool) Submit(task *StockFetchTask) error {
	p.mu.Lock()
	p.tasks[task.ID] = task
	p.mu.Unlock()

	select {
	case p.taskQueue <- task:
		logger.Info("Task submitted",
			zap.String("task_id", task.ID),
			zap.String("symbol", task.Symbol),
		)
		return nil
	case <-p.ctx.Done():
		return fmt.Errorf("worker pool is shutting down")
	default:
		return fmt.Errorf("task queue is full")
	}
}

// GetTaskStatus 獲取任務狀態
func (p *WorkerPool) GetTaskStatus(taskID string) (*StockFetchTask, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	task, exists := p.tasks[taskID]
	if !exists {
		return nil, fmt.Errorf("task not found: %s", taskID)
	}

	return task, nil
}

// GetAllTasks 獲取所有任務
func (p *WorkerPool) GetAllTasks() []*StockFetchTask {
	p.mu.RLock()
	defer p.mu.RUnlock()

	tasks := make([]*StockFetchTask, 0, len(p.tasks))
	for _, task := range p.tasks {
		tasks = append(tasks, task)
	}

	return tasks
}

// updateTaskStatus 更新任務狀態
func (p *WorkerPool) updateTaskStatus(taskID string, status TaskStatus) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if task, exists := p.tasks[taskID]; exists {
		task.Status = status
	}
}

// updateTaskError 更新任務錯誤
func (p *WorkerPool) updateTaskError(taskID string, err error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if task, exists := p.tasks[taskID]; exists {
		task.Error = err
	}
}

// Stop 停止 Worker Pool
func (p *WorkerPool) Stop() {
	logger.Info("Stopping worker pool")

	p.cancel()
	close(p.taskQueue)

	// 等待所有 Worker 完成
	p.wg.Wait()

	close(p.resultQueue)

	logger.Info("Worker pool stopped")
}

// Stats 獲取統計資訊
func (p *WorkerPool) Stats() map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()

	pending := 0
	running := 0
	completed := 0
	failed := 0

	for _, task := range p.tasks {
		switch task.Status {
		case TaskStatusPending:
			pending++
		case TaskStatusRunning:
			running++
		case TaskStatusCompleted:
			completed++
		case TaskStatusFailed:
			failed++
		}
	}

	return map[string]interface{}{
		"workers":        p.workers,
		"queue_size":     len(p.taskQueue),
		"total_tasks":    len(p.tasks),
		"pending_tasks":  pending,
		"running_tasks":  running,
		"completed_tasks": completed,
		"failed_tasks":   failed,
	}
}
