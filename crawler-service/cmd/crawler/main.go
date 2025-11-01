package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/stock-analysis/crawler-service/internal/config"
	"github.com/stock-analysis/crawler-service/internal/scraper"
	"github.com/stock-analysis/crawler-service/internal/storage"
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

	// 健康檢查所有券商
	ctx := context.Background()
	healthStatus := brokerManager.HealthCheckAll(ctx)
	healthyCount := 0
	for name, err := range healthStatus {
		if err != nil {
			logger.Warn("Broker health check failed",
				zap.String("broker", name),
				zap.Error(err),
			)
		} else {
			healthyCount++
			logger.Info("Broker is healthy",
				zap.String("broker", name),
			)
		}
	}

	logger.Info("Health check completed",
		zap.Int("healthy_brokers", healthyCount),
		zap.Int("total_brokers", len(healthStatus)),
	)

	// 初始化資料庫連線
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
	defer db.Close()

	// 檢查資料庫健康狀態
	dbHealthCtx, dbHealthCancel := context.WithTimeout(ctx, 5*time.Second)
	defer dbHealthCancel()

	if err := db.HealthCheck(dbHealthCtx); err != nil {
		logger.Fatal("Database health check failed", zap.Error(err))
	}
	logger.Info("Database connection healthy")

	// 初始化 Repository
	repo := storage.NewPostgresRepository(db)
	logger.Info("Repository initialized")

	// 初始化批次插入器（用於高效能批次操作）
	batchInserter, err := storage.NewBatchInserter(
		cfg.Database.URL,
		cfg.Database.MaxOpenConns,
		cfg.Crawler.BatchSize,
	)
	if err != nil {
		logger.Fatal("Failed to create batch inserter", zap.Error(err))
	}
	defer batchInserter.Close()
	logger.Info("Batch inserter initialized",
		zap.Int("batch_size", cfg.Crawler.BatchSize),
	)

	// TODO: 初始化 HTTP 服務器
	// router := api.SetupRouter(cfg, brokerManager, repo, batchInserter)
	// srv := &http.Server{
	//     Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
	//     Handler:      router,
	//     ReadTimeout:  cfg.Server.ReadTimeout,
	//     WriteTimeout: cfg.Server.WriteTimeout,
	// }

	// 示範：測試爬取並儲存到資料庫
	testSymbol := "2330"
	logger.Info("Testing fetch and save functionality", zap.String("symbol", testSymbol))

	fetchCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	result, err := brokerManager.FetchWithFailover(fetchCtx, testSymbol)
	if err != nil {
		logger.Error("Failed to fetch data", zap.Error(err))
	} else {
		logger.Info("Successfully fetched data",
			zap.String("symbol", result.Symbol),
			zap.String("source", result.Source),
			zap.Int("records", result.RecordCount),
			zap.Duration("duration", result.Duration),
		)

		// 如果成功爬取到資料，嘗試儲存到資料庫
		if len(result.Data) > 0 {
			logger.Info("Attempting to save data to database",
				zap.Int("record_count", len(result.Data)),
			)

			// 轉換為資料庫模型
			dbRecords := make([]storage.StockDailyData, 0, len(result.Data))
			for _, data := range result.Data {
				dbRecord := storage.StockDailyData{
					StockCode:   data.StockCode,
					TradeDate:   data.TradeDate,
					OpenPrice:   &data.OpenPrice,
					HighPrice:   &data.HighPrice,
					LowPrice:    &data.LowPrice,
					ClosePrice:  &data.ClosePrice,
					Volume:      &data.Volume,
					DataSource:  data.DataSource,
					DataQuality: &data.DataQuality,
					IsValidated: false,
				}

				// 計算成交額（如果沒有的話）
				if data.Volume > 0 && data.ClosePrice > 0 {
					turnover := float64(data.Volume) * data.ClosePrice / 1000.0 // 以千元為單位
					dbRecord.Turnover = &turnover
				}

				dbRecords = append(dbRecords, dbRecord)
			}

			// 使用批次插入器儲存（更高效）
			saveCtx, saveCancel := context.WithTimeout(ctx, 30*time.Second)
			defer saveCancel()

			rowsAffected, err := batchInserter.BatchUpsertWithRetry(saveCtx, dbRecords, 3)
			if err != nil {
				logger.Error("Failed to save data to database", zap.Error(err))
			} else {
				logger.Info("Successfully saved data to database",
					zap.Int64("rows_affected", rowsAffected),
				)

				// 驗證：從資料庫讀取最新資料
				verifyCtx, verifyCancel := context.WithTimeout(ctx, 5*time.Second)
				defer verifyCancel()

				latestData, err := repo.GetLatestDailyData(verifyCtx, testSymbol)
				if err != nil {
					logger.Error("Failed to verify saved data", zap.Error(err))
				} else if latestData != nil {
					logger.Info("Verified data from database",
						zap.String("stock_code", latestData.StockCode),
						zap.Time("trade_date", latestData.TradeDate),
						zap.Float64("close_price", *latestData.ClosePrice),
					)
				}
			}
		}
	}

	// 示範 HTTP 服務器（簡化版）
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	mux.HandleFunc("/api/v1/stocks/", func(w http.ResponseWriter, r *http.Request) {
		// 簡單示範
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"message":"Stock API endpoint - implementation pending"}`))
	})

	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      mux,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
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

	logger.Info("Shutting down server...")

	// 優雅關閉
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server forced to shutdown", zap.Error(err))
	}

	logger.Info("Server exited")
}
