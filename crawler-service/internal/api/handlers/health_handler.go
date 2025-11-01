package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/stock-analysis/crawler-service/internal/scraper"
	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// HealthHandler 健康檢查處理器
type HealthHandler struct {
	brokerManager *scraper.BrokerManager
	repository    storage.Repository
	batchService  *service.BatchService
}

// NewHealthHandler 創建健康檢查處理器
func NewHealthHandler(
	brokerManager *scraper.BrokerManager,
	repository storage.Repository,
	batchService *service.BatchService,
) *HealthHandler {
	return &HealthHandler{
		brokerManager: brokerManager,
		repository:    repository,
		batchService:  batchService,
	}
}

// HealthResponse 健康檢查響應
type HealthResponse struct {
	Status      string                 `json:"status"`
	Timestamp   time.Time              `json:"timestamp"`
	Database    DatabaseHealth         `json:"database"`
	Brokers     BrokersHealth          `json:"brokers"`
	Workers     map[string]interface{} `json:"workers"`
	Version     string                 `json:"version"`
}

// DatabaseHealth 資料庫健康資訊
type DatabaseHealth struct {
	Status    string `json:"status"`
	Connected bool   `json:"connected"`
	Message   string `json:"message,omitempty"`
}

// BrokersHealth 券商健康資訊
type BrokersHealth struct {
	TotalBrokers   int                    `json:"total_brokers"`
	HealthyBrokers int                    `json:"healthy_brokers"`
	Brokers        []BrokerHealthInfo     `json:"brokers"`
}

// BrokerHealthInfo 單個券商健康資訊
type BrokerHealthInfo struct {
	Name    string `json:"name"`
	Healthy bool   `json:"healthy"`
	Error   string `json:"error,omitempty"`
}

// HealthCheck 健康檢查
// GET /health
func (h *HealthHandler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	logger.Info("Handling HealthCheck request")

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	// 檢查資料庫
	dbHealth := h.checkDatabase(ctx)

	// 檢查券商
	brokersHealth := h.checkBrokers(ctx)

	// 獲取 Worker 統計
	workerStats := h.batchService.GetWorkerPoolStats()

	// 判斷整體狀態
	overallStatus := "ok"
	if !dbHealth.Connected {
		overallStatus = "degraded"
	}
	if brokersHealth.HealthyBrokers == 0 {
		overallStatus = "degraded"
	}

	response := HealthResponse{
		Status:    overallStatus,
		Timestamp: time.Now(),
		Database:  dbHealth,
		Brokers:   brokersHealth,
		Workers:   workerStats,
		Version:   "v1.0.0",
	}

	// 根據狀態設置 HTTP 狀態碼
	statusCode := http.StatusOK
	if overallStatus == "degraded" {
		statusCode = http.StatusServiceUnavailable
	}

	WriteJSON(w, statusCode, response)
}

// checkDatabase 檢查資料庫連線
func (h *HealthHandler) checkDatabase(ctx context.Context) DatabaseHealth {
	// 嘗試執行簡單查詢
	_, err := h.repository.GetLatestDailyData(ctx, "2330")

	if err != nil {
		// 如果是 not found 錯誤，連線實際上是正常的
		if err.Error() == "sql: no rows in result set" {
			return DatabaseHealth{
				Status:    "ok",
				Connected: true,
				Message:   "Connected (no data for test query)",
			}
		}

		logger.Error("Database health check failed", zap.Error(err))
		return DatabaseHealth{
			Status:    "error",
			Connected: false,
			Message:   err.Error(),
		}
	}

	return DatabaseHealth{
		Status:    "ok",
		Connected: true,
	}
}

// checkBrokers 檢查券商健康度
func (h *HealthHandler) checkBrokers(ctx context.Context) BrokersHealth {
	// 執行健康檢查
	healthResults := h.brokerManager.HealthCheckAll(ctx)

	brokerInfos := make([]BrokerHealthInfo, 0, len(healthResults))
	healthyCount := 0

	for brokerName, err := range healthResults {
		isHealthy := err == nil
		errorMsg := ""

		if !isHealthy {
			errorMsg = err.Error()
		} else {
			healthyCount++
		}

		brokerInfos = append(brokerInfos, BrokerHealthInfo{
			Name:    brokerName,
			Healthy: isHealthy,
			Error:   errorMsg,
		})
	}

	return BrokersHealth{
		TotalBrokers:   len(healthResults),
		HealthyBrokers: healthyCount,
		Brokers:        brokerInfos,
	}
}
