package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StockListHandler 股票清單處理器
type StockListHandler struct {
	stockListService *service.StockListService
}

// NewStockListHandler 建立股票清單處理器
func NewStockListHandler(stockListService *service.StockListService) *StockListHandler {
	return &StockListHandler{
		stockListService: stockListService,
	}
}

// FetchAllStocks 爬取所有股票清單
// POST /api/v1/stocks/fetch-all
func (h *StockListHandler) FetchAllStocks(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		WriteError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Only POST method is allowed")
		return
	}

	logger.Info("收到爬取所有股票清單請求")

	// 建立帶超時的 context
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Minute)
	defer cancel()

	// 執行爬取
	count, err := h.stockListService.FetchAllStocks(ctx)
	if err != nil {
		logger.Error("爬取股票清單失敗", zap.Error(err))
		WriteInternalError(w, "Failed to fetch stock list: "+err.Error())
		return
	}

	// 回傳成功結果
	response := map[string]interface{}{
		"message":      "股票清單爬取完成",
		"total_stocks": count,
		"timestamp":    time.Now(),
	}

	logger.Info("股票清單爬取成功", zap.Int("count", count))
	WriteSuccess(w, response)
}
