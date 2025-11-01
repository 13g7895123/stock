package handlers

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StockHandler 股票處理器
type StockHandler struct {
	stockService *service.StockService
}

// NewStockHandler 創建股票處理器
func NewStockHandler(stockService *service.StockService) *StockHandler {
	return &StockHandler{
		stockService: stockService,
	}
}

// GetStockDaily 獲取股票日線資料
// GET /api/v1/stocks/{symbol}/daily?broker={broker}
func (h *StockHandler) GetStockDaily(w http.ResponseWriter, r *http.Request) {
	// 解析路徑參數
	pathParts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(pathParts) < 4 {
		WriteBadRequest(w, "Invalid path: missing stock symbol")
		return
	}

	symbol := pathParts[3] // /api/v1/stocks/{symbol}/daily
	if symbol == "" {
		WriteBadRequest(w, "Stock symbol is required")
		return
	}

	// 解析查詢參數
	broker := r.URL.Query().Get("broker")

	logger.Info("Handling GetStockDaily request",
		zap.String("symbol", symbol),
		zap.String("broker", broker),
	)

	// 調用服務層
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Minute)
	defer cancel()

	response, err := h.stockService.FetchStockDaily(ctx, symbol, broker)
	if err != nil {
		logger.Error("Failed to fetch stock daily data",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		WriteInternalError(w, "Failed to fetch stock data: "+err.Error())
		return
	}

	WriteSuccess(w, response)
}

// GetStockHistory 獲取股票歷史資料
// GET /api/v1/stocks/{symbol}/history?start={date}&end={date}
func (h *StockHandler) GetStockHistory(w http.ResponseWriter, r *http.Request) {
	// 解析路徑參數
	pathParts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(pathParts) < 4 {
		WriteBadRequest(w, "Invalid path: missing stock symbol")
		return
	}

	symbol := pathParts[3] // /api/v1/stocks/{symbol}/history
	if symbol == "" {
		WriteBadRequest(w, "Stock symbol is required")
		return
	}

	// 解析查詢參數
	startDateStr := r.URL.Query().Get("start")
	endDateStr := r.URL.Query().Get("end")

	// 預設日期範圍（最近 30 天）
	endDate := time.Now()
	startDate := endDate.AddDate(0, 0, -30)

	// 解析開始日期
	if startDateStr != "" {
		parsed, err := time.Parse("2006-01-02", startDateStr)
		if err != nil {
			WriteBadRequest(w, "Invalid start date format. Use YYYY-MM-DD")
			return
		}
		startDate = parsed
	}

	// 解析結束日期
	if endDateStr != "" {
		parsed, err := time.Parse("2006-01-02", endDateStr)
		if err != nil {
			WriteBadRequest(w, "Invalid end date format. Use YYYY-MM-DD")
			return
		}
		endDate = parsed
	}

	logger.Info("Handling GetStockHistory request",
		zap.String("symbol", symbol),
		zap.Time("start_date", startDate),
		zap.Time("end_date", endDate),
	)

	// 調用服務層
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	records, err := h.stockService.GetStockHistory(ctx, symbol, startDate, endDate)
	if err != nil {
		logger.Error("Failed to get stock history",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		WriteInternalError(w, "Failed to get history: "+err.Error())
		return
	}

	responseData := map[string]interface{}{
		"symbol":      symbol,
		"start_date":  startDate.Format("2006-01-02"),
		"end_date":    endDate.Format("2006-01-02"),
		"record_count": len(records),
		"records":     records,
	}

	WriteSuccess(w, responseData)
}

// GetLatestData 獲取最新資料
// GET /api/v1/stocks/{symbol}/latest
func (h *StockHandler) GetLatestData(w http.ResponseWriter, r *http.Request) {
	// 解析路徑參數
	pathParts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(pathParts) < 4 {
		WriteBadRequest(w, "Invalid path: missing stock symbol")
		return
	}

	symbol := pathParts[3]
	if symbol == "" {
		WriteBadRequest(w, "Stock symbol is required")
		return
	}

	logger.Info("Handling GetLatestData request",
		zap.String("symbol", symbol),
	)

	// 調用服務層
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	data, err := h.stockService.GetLatestData(ctx, symbol)
	if err != nil {
		logger.Error("Failed to get latest data",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		WriteNotFound(w, "No data found for symbol: "+symbol)
		return
	}

	WriteSuccess(w, data)
}
