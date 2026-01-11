package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StatsHandler 統計資料處理器
type StatsHandler struct {
	repository storage.Repository
}

// NewStatsHandler 創建統計資料處理器
func NewStatsHandler(repository storage.Repository) *StatsHandler {
	return &StatsHandler{
		repository: repository,
	}
}

// StocksSummaryResponse 股票統計響應
type StocksSummaryResponse struct {
	TotalStocks  int                         `json:"total_stocks"`
	TotalRecords int                         `json:"total_records"`
	Stocks       []storage.StockSummaryItem  `json:"stocks"`
	Timestamp    time.Time                   `json:"timestamp"`
}

// GetStocksSummary 獲取股票資料統計
// GET /api/v1/stats/stocks-summary
func (h *StatsHandler) GetStocksSummary(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		WriteError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Only GET method is allowed")
		return
	}

	logger.Info("Handling GetStocksSummary request")

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	// 獲取統計資料
	summary, err := h.repository.GetStocksSummary(ctx)
	if err != nil {
		logger.Error("Failed to get stocks summary",
			zap.Error(err),
		)
		WriteError(w, http.StatusInternalServerError, "DATABASE_ERROR", "Failed to retrieve statistics")
		return
	}

	// 計算總計
	totalRecords := 0
	for _, item := range summary {
		totalRecords += item.RecordCount
	}

	response := StocksSummaryResponse{
		TotalStocks:  len(summary),
		TotalRecords: totalRecords,
		Stocks:       summary,
		Timestamp:    time.Now(),
	}

	logger.Info("Successfully retrieved stocks summary",
		zap.Int("total_stocks", len(summary)),
		zap.Int("total_records", totalRecords),
	)

	WriteJSON(w, http.StatusOK, response)
}
