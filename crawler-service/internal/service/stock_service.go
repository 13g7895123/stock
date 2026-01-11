package service

import (
	"context"
	"fmt"
	"time"

	"github.com/stock-analysis/crawler-service/internal/scraper"
	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StockService 股票資料服務
type StockService struct {
	brokerManager *scraper.BrokerManager
	repository    storage.Repository
	batchInserter *storage.BatchInserter
	validator     *scraper.Validator
}

// NewStockService 創建股票服務
func NewStockService(
	brokerManager *scraper.BrokerManager,
	repository storage.Repository,
	batchInserter *storage.BatchInserter,
) *StockService {
	return &StockService{
		brokerManager: brokerManager,
		repository:    repository,
		batchInserter: batchInserter,
		validator:     scraper.NewValidator(),
	}
}

// FetchStockDailyResponse 股票日線資料響應
type FetchStockDailyResponse struct {
	Symbol      string                `json:"symbol"`
	Source      string                `json:"source"`
	RecordCount int                   `json:"record_count"`
	Records     []storage.StockDailyData `json:"records"`
	Duration    time.Duration         `json:"duration_ms"`
	FetchedAt   time.Time             `json:"fetched_at"`
}

// FetchStockDaily 即時爬取股票日線資料
func (s *StockService) FetchStockDaily(ctx context.Context, symbol string, broker string) (interface{}, error) {
	startTime := time.Now()

	logger.Info("Fetching stock daily data",
		zap.String("symbol", symbol),
		zap.String("broker", broker),
	)

	// 爬取資料（目前不支持指定券商，使用自動容錯）
	result, err := s.brokerManager.FetchWithFailover(ctx, symbol)

	if err != nil {
		logger.Error("Failed to fetch stock data",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		return nil, fmt.Errorf("failed to fetch data: %w", err)
	}

	// 驗證資料
	validRecords := []scraper.DailyData{}
	for _, record := range result.Data {
		if err := s.validator.Validate(&record); err == nil {
			validRecords = append(validRecords, record)
		}
	}

	logger.Info("Data validation completed",
		zap.Int("total", len(result.Data)),
		zap.Int("valid", len(validRecords)),
	)

	// 轉換為儲存格式
	dbRecords := make([]storage.StockDailyData, len(validRecords))
	for i, record := range validRecords {
		// Create local copies to avoid pointer aliasing issues
		rec := record // Important: create a copy of the loop variable
		
		dataQuality := rec.DataQuality
		if dataQuality == "" {
			dataQuality = "raw"
		}
		dbRecords[i] = storage.StockDailyData{
			StockCode:    rec.StockCode,
			TradeDate:    rec.TradeDate,
			OpenPrice:    &rec.OpenPrice,
			HighPrice:    &rec.HighPrice,
			LowPrice:     &rec.LowPrice,
			ClosePrice:   &rec.ClosePrice,
			Volume:       &rec.Volume,
			Turnover:     &rec.Turnover,
			DataSource:   result.Source,
			DataQuality:  &dataQuality,
			IsValidated:  true,
		}
	}

	// 保存到資料庫（使用批次 Upsert 避免重複）
	if len(dbRecords) > 0 {
		saveCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
		defer cancel()

		rowsAffected, err := s.batchInserter.BatchUpsertWithRetry(saveCtx, dbRecords, 3)
		if err != nil {
			logger.Error("Failed to save data",
				zap.String("symbol", symbol),
				zap.Error(err),
			)
			// 不返回錯誤，爬取的資料仍然返回給客戶端
		} else {
			logger.Info("Data saved successfully",
				zap.String("symbol", symbol),
				zap.Int64("rows_affected", rowsAffected),
			)
		}
	}

	duration := time.Since(startTime)

	response := &FetchStockDailyResponse{
		Symbol:      result.Symbol,
		Source:      result.Source,
		RecordCount: len(dbRecords),
		Records:     dbRecords,
		Duration:    duration,
		FetchedAt:   time.Now(),
	}

	return response, nil
}

// GetStockHistory 獲取股票歷史資料
func (s *StockService) GetStockHistory(ctx context.Context, symbol string, startDate, endDate time.Time) ([]storage.StockDailyData, error) {
	logger.Info("Querying stock history",
		zap.String("symbol", symbol),
		zap.Time("start_date", startDate),
		zap.Time("end_date", endDate),
	)

	records, err := s.repository.GetDailyDataRange(ctx, symbol, startDate, endDate)
	if err != nil {
		logger.Error("Failed to query history",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		return nil, fmt.Errorf("failed to query history: %w", err)
	}

	logger.Info("History query completed",
		zap.String("symbol", symbol),
		zap.Int("records", len(records)),
	)

	return records, nil
}

// GetLatestData 獲取最新資料
func (s *StockService) GetLatestData(ctx context.Context, symbol string) (*storage.StockDailyData, error) {
	logger.Info("Querying latest data",
		zap.String("symbol", symbol),
	)

	data, err := s.repository.GetLatestDailyData(ctx, symbol)
	if err != nil {
		logger.Error("Failed to query latest data",
			zap.String("symbol", symbol),
			zap.Error(err),
		)
		return nil, fmt.Errorf("failed to query latest data: %w", err)
	}

	return data, nil
}

// GetDataQuality 獲取資料品質統計
func (s *StockService) GetDataQuality(ctx context.Context, symbol string) (map[string]interface{}, error) {
	stats, err := s.repository.GetDataQualityStats(ctx, symbol)
	if err != nil {
		return nil, fmt.Errorf("failed to get quality stats: %w", err)
	}

	// 轉換 map[string]int 為 map[string]interface{}
	result := make(map[string]interface{})
	for k, v := range stats {
		result[k] = v
	}

	return result, nil
}
