package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/stock-analysis/crawler-service/internal/api"
	"github.com/stock-analysis/crawler-service/internal/api/middleware"
	"github.com/stock-analysis/crawler-service/internal/config"
	"github.com/stock-analysis/crawler-service/internal/metrics"
	"github.com/stock-analysis/crawler-service/internal/scraper"
	"github.com/stock-analysis/crawler-service/internal/service"
	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/internal/worker"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

const (
	appName    = "stock-crawler-service"
	appVersion = "v1.0.0"
)

func main() {
	// 載入配置
	cfg, err := config.LoadFromEnv()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load config: %v\n", err)
		os.Exit(1)
	}

	// 初始化日誌
	if err := logger.Init(
		cfg.Logging.Level,
		cfg.Logging.Format,
		cfg.Logging.Output,
		cfg.Logging.FilePath,
	); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize logger: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	logger.Info("Starting application",
		zap.String("app", appName),
		zap.String("version", appVersion),
	)

	// 建立爬蟲管理器
	brokerManager := scraper.NewBrokerManager(
		cfg.Crawler.BrokerURLs,
		cfg.Crawler.RequestTimeout,
		cfg.Crawler.RetryCount,
	)

	logger.Info("Broker manager initialized",
		zap.Int("broker_count", len(cfg.Crawler.BrokerURLs)),
	)

	// 券商健康檢查
	healthCtx, healthCancel := context.WithTimeout(context.Background(), 30*time.Second)
	brokerManager.HealthCheckAll(healthCtx)
	healthCancel()

	// 連線資料庫
	logger.Info("Connecting to database...")
	dbConfig := &storage.PostgresConfig{
		Host:            cfg.Database.Host,
		Port:            cfg.Database.Port,
		User:            cfg.Database.User,
		Password:        cfg.Database.Password,
		Database:        cfg.Database.Database,
		SSLMode:         cfg.Database.SSLMode,
		MaxOpenConns:    cfg.Database.MaxOpenConns,
		MaxIdleConns:    cfg.Database.MaxIdleConns,
		ConnMaxLifetime: cfg.Database.ConnMaxLifetime,
		ConnMaxIdleTime: cfg.Database.ConnMaxIdleTime,
	}

	db, err := storage.NewPostgresDB(dbConfig)
	if err != nil {
		logger.Fatal("Failed to connect to database", zap.Error(err))
	}

	// 驗證資料庫連線
	ctx := context.Background()
	if err := db.Ping(ctx); err != nil {
		logger.Fatal("Failed to ping database", zap.Error(err))
	}

	logger.Info("Database connection healthy")

	// 建立 Repository
	repository := storage.NewPostgresRepository(db)
	logger.Info("Repository initialized")

	// 建立批次插入器
	// 構建 database URL
	dbURL := fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Host,
		cfg.Database.Port,
		cfg.Database.Database,
		cfg.Database.SSLMode,
	)
	batchInserter, err := storage.NewBatchInserter(
		dbURL,
		cfg.Database.MaxOpenConns,
		cfg.Crawler.BatchSize,
	)
	if err != nil {
		logger.Fatal("Failed to create batch inserter", zap.Error(err))
	}
	logger.Info("Batch inserter initialized",
		zap.Int("batch_size", cfg.Crawler.BatchSize),
	)

	// 初始化 Metrics
	appMetrics := metrics.NewMetrics()
	logger.Info("Metrics initialized")

	// 建立服務層
	stockService := service.NewStockService(
		brokerManager,
		repository,
		batchInserter,
	)
	logger.Info("Stock service initialized")

	// 建立 Worker Pool
	workerPool := worker.NewWorkerPool(
		cfg.Crawler.MaxWorkers,
		stockService,
	)
	workerPool.Start()
	logger.Info("Worker pool started",
		zap.Int("workers", cfg.Crawler.MaxWorkers),
	)

	// 建立批次服務
	batchService := service.NewBatchService(workerPool)
	logger.Info("Batch service initialized")

	// 配置 CORS
	corsConfig := &middleware.CORSConfig{
		AllowedOrigins: cfg.Server.CORS.AllowedOrigins,
		AllowedMethods: cfg.Server.CORS.AllowedMethods,
		AllowedHeaders: cfg.Server.CORS.AllowedHeaders,
		MaxAge:         cfg.Server.CORS.MaxAge,
	}

	if len(corsConfig.AllowedOrigins) == 0 {
		corsConfig = middleware.DefaultCORSConfig()
	}

	// 創建路由器
	routerConfig := &api.RouterConfig{
		StockService:  stockService,
		BatchService:  batchService,
		BrokerManager: brokerManager,
		Repository:    repository,
		CORSConfig:    corsConfig,
	}

	handler := api.NewRouter(routerConfig)
	logger.Info("Router initialized")

	// 創建 HTTP 服務器
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      handler,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}

	// 啟動 Metrics 服務器（如果啟用）
	if cfg.Metrics.Enabled {
		metricsServer := &http.Server{
			Addr:    fmt.Sprintf(":%d", cfg.Metrics.Port),
			Handler: appMetrics.Handler(),
		}

		go func() {
			logger.Info("Starting metrics server",
				zap.Int("port", cfg.Metrics.Port),
			)
			if err := metricsServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
				logger.Error("Metrics server error", zap.Error(err))
			}
		}()

		// 在關閉時也停止 metrics 服務器
		defer func() {
			shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			if err := metricsServer.Shutdown(shutdownCtx); err != nil {
				logger.Error("Failed to shutdown metrics server", zap.Error(err))
			}
		}()
	}

	// 啟動 HTTP 服務器
	go func() {
		logger.Info("Starting HTTP server",
			zap.String("addr", srv.Addr),
		)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// 等待中斷信號
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down gracefully...")

	// 停止 Worker Pool
	workerPool.Stop()

	// 關閉 HTTP 服務器
	shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server forced to shutdown", zap.Error(err))
	}

	// 關閉資料庫連線
	if err := db.Close(); err != nil {
		logger.Error("Failed to close database", zap.Error(err))
	}

	logger.Info("Server stopped")
}
