package storage

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// BatchInserter provides high-performance batch insert using PostgreSQL COPY protocol
type BatchInserter struct {
	pool      *pgxpool.Pool
	batchSize int
}

// NewBatchInserter creates a new batch inserter
func NewBatchInserter(databaseURL string, maxConns int, batchSize int) (*BatchInserter, error) {
	config, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	// Configure connection pool
	config.MaxConns = int32(maxConns)
	config.MinConns = int32(maxConns / 4)
	config.MaxConnLifetime = time.Hour
	config.MaxConnIdleTime = 10 * time.Minute

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	logger.Info("Batch inserter initialized",
		zap.Int("max_conns", maxConns),
		zap.Int("batch_size", batchSize),
	)

	return &BatchInserter{
		pool:      pool,
		batchSize: batchSize,
	}, nil
}

// BatchInsertDailyData performs high-speed batch insert using COPY protocol
func (b *BatchInserter) BatchInsertDailyData(ctx context.Context, data []StockDailyData) (int64, error) {
	if len(data) == 0 {
		return 0, nil
	}

	start := time.Now()
	logger.Info("Starting batch insert", zap.Int("record_count", len(data)))

	// Get a connection from the pool
	conn, err := b.pool.Acquire(ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to acquire connection: %w", err)
	}
	defer conn.Release()

	// Start COPY transaction using PostgreSQL COPY protocol
	rowsAffected, err := conn.Conn().CopyFrom(
		ctx,
		pgx.Identifier{"stock_daily_data"},
		[]string{
			"stock_code", "trade_date", "open_price", "high_price", "low_price", "close_price",
			"volume", "turnover", "data_source", "data_quality", "is_validated", "created_at",
		},
		pgx.CopyFromSlice(len(data), func(i int) ([]interface{}, error) {
			d := &data[i]
			return []interface{}{
				d.StockCode,
				d.TradeDate,
				d.OpenPrice,
				d.HighPrice,
				d.LowPrice,
				d.ClosePrice,
				d.Volume,
				d.Turnover,
				d.DataSource,
				d.DataQuality,
				d.IsValidated,
				time.Now(), // created_at
			}, nil
		}),
	)

	if err != nil {
		return 0, fmt.Errorf("COPY failed: %w", err)
	}

	duration := time.Since(start)
	logger.Info("Batch insert completed",
		zap.Int64("rows_inserted", rowsAffected),
		zap.Int64("duration_ms", duration.Milliseconds()),
		zap.Float64("rows_per_sec", float64(rowsAffected)/duration.Seconds()),
	)

	return rowsAffected, nil
}

// BatchUpsertDailyData performs batch upsert with ON CONFLICT
// This is slower than COPY but handles duplicates
func (b *BatchInserter) BatchUpsertDailyData(ctx context.Context, data []StockDailyData) (int64, error) {
	if len(data) == 0 {
		return 0, nil
	}

	start := time.Now()
	logger.Info("Starting batch upsert", zap.Int("record_count", len(data)))

	var totalAffected int64

	// Process in batches to avoid excessive memory usage
	for i := 0; i < len(data); i += b.batchSize {
		end := i + b.batchSize
		if end > len(data) {
			end = len(data)
		}

		batch := data[i:end]
		affected, err := b.batchUpsertChunk(ctx, batch)
		if err != nil {
			return totalAffected, fmt.Errorf("failed to upsert batch %d-%d: %w", i, end, err)
		}

		totalAffected += affected
	}

	duration := time.Since(start)
	logger.Info("Batch upsert completed",
		zap.Int64("rows_affected", totalAffected),
		zap.Int64("duration_ms", duration.Milliseconds()),
		zap.Float64("rows_per_sec", float64(totalAffected)/duration.Seconds()),
	)

	return totalAffected, nil
}

// batchUpsertChunk performs upsert for a single chunk of data
func (b *BatchInserter) batchUpsertChunk(ctx context.Context, data []StockDailyData) (int64, error) {
	if len(data) == 0 {
		return 0, nil
	}

	// Build multi-row INSERT statement
	valueStrings := make([]string, 0, len(data))
	valueArgs := make([]interface{}, 0, len(data)*11)

	for i, d := range data {
		offset := i * 11
		valueStrings = append(valueStrings, fmt.Sprintf(
			"($%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, $%d, NOW())",
			offset+1, offset+2, offset+3, offset+4, offset+5, offset+6,
			offset+7, offset+8, offset+9, offset+10, offset+11,
		))

		// Dereference pointers and provide default values for nil
		var openPrice, highPrice, lowPrice, closePrice, turnover float64
		var volume int64
		var dataQuality string

		if d.OpenPrice != nil {
			openPrice = *d.OpenPrice
		}
		if d.HighPrice != nil {
			highPrice = *d.HighPrice
		}
		if d.LowPrice != nil {
			lowPrice = *d.LowPrice
		}
		if d.ClosePrice != nil {
			closePrice = *d.ClosePrice
		}
		if d.Volume != nil {
			volume = *d.Volume
		}
		if d.Turnover != nil {
			turnover = *d.Turnover
		}
		if d.DataQuality != nil {
			dataQuality = *d.DataQuality
		} else {
			dataQuality = "raw"
		}

		valueArgs = append(valueArgs,
			d.StockCode,
			d.TradeDate,
			openPrice,
			highPrice,
			lowPrice,
			closePrice,
			volume,
			turnover,
			d.DataSource,
			dataQuality,
			d.IsValidated,
		)
	}

	query := fmt.Sprintf(`
		INSERT INTO stock_daily_data (
			stock_code, trade_date, open_price, high_price, low_price, close_price,
			volume, turnover, data_source, data_quality, is_validated, created_at
		) VALUES %s
		ON CONFLICT (stock_code, trade_date) DO UPDATE SET
			open_price = EXCLUDED.open_price,
			high_price = EXCLUDED.high_price,
			low_price = EXCLUDED.low_price,
			close_price = EXCLUDED.close_price,
			volume = EXCLUDED.volume,
			turnover = EXCLUDED.turnover,
			data_source = EXCLUDED.data_source,
			data_quality = EXCLUDED.data_quality,
			is_validated = EXCLUDED.is_validated,
			updated_at = NOW()
	`, strings.Join(valueStrings, ","))

	// Execute the query
	result, err := b.pool.Exec(ctx, query, valueArgs...)
	if err != nil {
		return 0, fmt.Errorf("failed to execute batch upsert: %w", err)
	}

	return result.RowsAffected(), nil
}

// BulkDelete deletes data in bulk based on criteria
func (b *BatchInserter) BulkDelete(ctx context.Context, stockCode string, startDate, endDate time.Time) (int64, error) {
	query := `
		DELETE FROM stock_daily_data
		WHERE stock_code = $1 AND trade_date BETWEEN $2 AND $3
	`

	result, err := b.pool.Exec(ctx, query, stockCode, startDate, endDate)
	if err != nil {
		return 0, fmt.Errorf("bulk delete failed: %w", err)
	}

	rowsAffected := result.RowsAffected()
	logger.Info("Bulk delete completed",
		zap.String("stock_code", stockCode),
		zap.String("start_date", startDate.Format("2006-01-02")),
		zap.String("end_date", endDate.Format("2006-01-02")),
		zap.Int64("rows_deleted", rowsAffected),
	)

	return rowsAffected, nil
}

// BulkUpdate updates data quality in bulk
func (b *BatchInserter) BulkUpdate(ctx context.Context, stockCode string, oldQuality, newQuality string) (int64, error) {
	query := `
		UPDATE stock_daily_data
		SET data_quality = $3, updated_at = NOW()
		WHERE stock_code = $1 AND data_quality = $2
	`

	result, err := b.pool.Exec(ctx, query, stockCode, oldQuality, newQuality)
	if err != nil {
		return 0, fmt.Errorf("bulk update failed: %w", err)
	}

	rowsAffected := result.RowsAffected()
	logger.Info("Bulk update completed",
		zap.String("stock_code", stockCode),
		zap.String("old_quality", oldQuality),
		zap.String("new_quality", newQuality),
		zap.Int64("rows_updated", rowsAffected),
	)

	return rowsAffected, nil
}

// GetConnectionStats returns connection pool statistics
func (b *BatchInserter) GetConnectionStats() map[string]interface{} {
	stats := b.pool.Stat()
	return map[string]interface{}{
		"total_conns":           stats.TotalConns(),
		"acquired_conns":        stats.AcquiredConns(),
		"idle_conns":            stats.IdleConns(),
		"max_conns":             stats.MaxConns(),
		"acquire_count":         stats.AcquireCount(),
		"acquire_duration_ms":   stats.AcquireDuration().Milliseconds(),
		"empty_acquire_count":   stats.EmptyAcquireCount(),
		"canceled_acquire_count": stats.CanceledAcquireCount(),
	}
}

// HealthCheck verifies the batch inserter is healthy
func (b *BatchInserter) HealthCheck(ctx context.Context) error {
	if err := b.pool.Ping(ctx); err != nil {
		return fmt.Errorf("batch inserter health check failed: %w", err)
	}
	return nil
}

// Close closes the connection pool
func (b *BatchInserter) Close() {
	if b.pool != nil {
		logger.Info("Closing batch inserter connection pool")
		b.pool.Close()
	}
}

// BatchInsertWithRetry performs batch insert with retry logic
func (b *BatchInserter) BatchInsertWithRetry(ctx context.Context, data []StockDailyData, maxRetries int) (int64, error) {
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			logger.Info("Retrying batch insert",
				zap.Int("attempt", attempt),
				zap.Int("max_retries", maxRetries),
			)
			// Exponential backoff
			backoff := time.Duration(attempt) * time.Second
			time.Sleep(backoff)
		}

		rowsAffected, err := b.BatchInsertDailyData(ctx, data)
		if err == nil {
			return rowsAffected, nil
		}

		lastErr = err
		logger.Error("Batch insert failed",
			zap.Int("attempt", attempt),
			zap.Error(err),
		)
	}

	return 0, fmt.Errorf("batch insert failed after %d retries: %w", maxRetries, lastErr)
}

// BatchUpsertWithRetry performs batch upsert with retry logic
func (b *BatchInserter) BatchUpsertWithRetry(ctx context.Context, data []StockDailyData, maxRetries int) (int64, error) {
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			logger.Info("Retrying batch upsert",
				zap.Int("attempt", attempt),
				zap.Int("max_retries", maxRetries),
			)
			// Exponential backoff
			backoff := time.Duration(attempt) * time.Second
			time.Sleep(backoff)
		}

		rowsAffected, err := b.BatchUpsertDailyData(ctx, data)
		if err == nil {
			return rowsAffected, nil
		}

		lastErr = err
		logger.Error("Batch upsert failed",
			zap.Int("attempt", attempt),
			zap.Error(err),
		)
	}

	return 0, fmt.Errorf("batch upsert failed after %d retries: %w", maxRetries, lastErr)
}
