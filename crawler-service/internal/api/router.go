package api

import (
	"net/http"

	"github.com/stock-analysis/crawler-service/internal/api/handlers"
	"github.com/stock-analysis/crawler-service/internal/api/middleware"
	"github.com/stock-analysis/crawler-service/internal/scraper"
	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// RouterConfig 路由配置
type RouterConfig struct {
	StockService  *service.StockService
	BatchService  *service.BatchService
	BrokerManager *scraper.BrokerManager
	Repository    storage.Repository
	CORSConfig    *middleware.CORSConfig
}

// NewRouter 創建新的路由器
func NewRouter(config *RouterConfig) http.Handler {
	// 創建處理器
	stockHandler := handlers.NewStockHandler(config.StockService)
	batchHandler := handlers.NewBatchHandler(config.BatchService)
	healthHandler := handlers.NewHealthHandler(
		config.BrokerManager,
		config.Repository,
		config.BatchService,
	)

	// 創建基礎路由器
	mux := http.NewServeMux()

	// 健康檢查
	mux.HandleFunc("/health", healthHandler.HealthCheck)

	// API v1 路由
	// 股票資料
	mux.HandleFunc("/api/v1/stocks/", func(w http.ResponseWriter, r *http.Request) {
		// 路由到對應的處理器
		path := r.URL.Path

		// /api/v1/stocks/{symbol}/daily
		if contains(path, "/daily") {
			stockHandler.GetStockDaily(w, r)
			return
		}

		// /api/v1/stocks/{symbol}/history
		if contains(path, "/history") {
			stockHandler.GetStockHistory(w, r)
			return
		}

		// /api/v1/stocks/{symbol}/latest
		if contains(path, "/latest") {
			stockHandler.GetLatestData(w, r)
			return
		}

		// /api/v1/stocks/batch-update
		if path == "/api/v1/stocks/batch-update" {
			batchHandler.BatchUpdate(w, r)
			return
		}

		// 未找到路由
		handlers.WriteNotFound(w, "Endpoint not found")
	})

	// 批次管理
	mux.HandleFunc("/api/v1/batch/", batchHandler.GetBatchStatus)

	// Worker 統計
	mux.HandleFunc("/api/v1/workers/stats", batchHandler.GetWorkerStats)

	// Prometheus metrics（如果啟用）
	// mux.Handle("/metrics", promhttp.Handler())

	// 應用中間件
	var handler http.Handler = mux

	// CORS 中間件
	if config.CORSConfig != nil {
		handler = middleware.CORS(config.CORSConfig)(handler)
		logger.Info("CORS middleware enabled")
	}

	// 日誌中間件
	handler = loggingMiddleware(handler)

	// 恢復中間件（panic recovery）
	handler = recoveryMiddleware(handler)

	return handler
}

// loggingMiddleware 日誌中間件
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := logger.Now()

		// 包裝 ResponseWriter 以捕獲狀態碼
		lw := &loggingResponseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
		}

		next.ServeHTTP(lw, r)

		duration := logger.Since(start)

		logger.Info("HTTP Request",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.Int("status", lw.statusCode),
			zap.Duration("duration", duration),
			zap.String("remote_addr", r.RemoteAddr),
		)
	})
}

// loggingResponseWriter 記錄響應的 ResponseWriter
type loggingResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (lw *loggingResponseWriter) WriteHeader(code int) {
	lw.statusCode = code
	lw.ResponseWriter.WriteHeader(code)
}

// recoveryMiddleware 恢復中間件
func recoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				logger.Error("Panic recovered",
					zap.Any("error", err),
					zap.String("method", r.Method),
					zap.String("path", r.URL.Path),
				)
				handlers.WriteInternalError(w, "Internal server error")
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// contains 檢查字串是否包含子字串
func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[len(s)-len(substr):] == substr ||
		   (len(s) > len(substr) && s[len(s)-len(substr)-1:len(s)-len(substr)] == "/")
}
