package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// BatchHandler 批次處理器
type BatchHandler struct {
	batchService *service.BatchService
}

// NewBatchHandler 創建批次處理器
func NewBatchHandler(batchService *service.BatchService) *BatchHandler {
	return &BatchHandler{
		batchService: batchService,
	}
}

// BatchUpdate 批次更新股票資料
// POST /api/v1/stocks/batch-update
// Body: {"symbols": ["2330", "2317", ...], "broker": "optional"}
func (h *BatchHandler) BatchUpdate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		WriteError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Only POST method is allowed")
		return
	}

	// 解析請求體
	var req service.BatchUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		WriteBadRequest(w, "Invalid request body: "+err.Error())
		return
	}

	// 驗證請求
	if len(req.Symbols) == 0 {
		WriteBadRequest(w, "Symbols array cannot be empty")
		return
	}

	logger.Info("Handling BatchUpdate request",
		zap.Int("symbol_count", len(req.Symbols)),
		zap.String("broker", req.Broker),
	)

	// 調用服務層
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	response, err := h.batchService.BatchUpdateStocks(ctx, &req)
	if err != nil {
		logger.Error("Failed to start batch update",
			zap.Error(err),
		)
		WriteInternalError(w, "Failed to start batch update: "+err.Error())
		return
	}

	WriteSuccess(w, response)
}

// GetBatchStatus 獲取批次狀態
// GET /api/v1/batch/{batchID}
func (h *BatchHandler) GetBatchStatus(w http.ResponseWriter, r *http.Request) {
	// 解析路徑參數
	pathParts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(pathParts) < 4 {
		WriteBadRequest(w, "Invalid path: missing batch ID")
		return
	}

	batchID := pathParts[3] // /api/v1/batch/{batchID}
	if batchID == "" {
		WriteBadRequest(w, "Batch ID is required")
		return
	}

	logger.Info("Handling GetBatchStatus request",
		zap.String("batch_id", batchID),
	)

	// 調用服務層
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	status, err := h.batchService.GetBatchStatus(ctx, batchID)
	if err != nil {
		logger.Error("Failed to get batch status",
			zap.String("batch_id", batchID),
			zap.Error(err),
		)
		WriteNotFound(w, "Batch not found: "+batchID)
		return
	}

	WriteSuccess(w, status)
}

// GetWorkerStats 獲取 Worker Pool 統計
// GET /api/v1/workers/stats
func (h *BatchHandler) GetWorkerStats(w http.ResponseWriter, r *http.Request) {
	logger.Info("Handling GetWorkerStats request")

	stats := h.batchService.GetWorkerPoolStats()

	WriteSuccess(w, stats)
}
