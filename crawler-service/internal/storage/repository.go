package storage

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// Repository defines the interface for stock data operations
type Repository interface {
	// StockDailyData operations
	CreateDailyData(ctx context.Context, data *StockDailyData) error
	CreateDailyDataBatch(ctx context.Context, data []StockDailyData) error
	GetDailyData(ctx context.Context, stockCode string, tradeDate time.Time) (*StockDailyData, error)
	GetDailyDataRange(ctx context.Context, stockCode string, startDate, endDate time.Time) ([]StockDailyData, error)
	GetLatestDailyData(ctx context.Context, stockCode string) (*StockDailyData, error)
	UpdateDailyData(ctx context.Context, data *StockDailyData) error
	DeleteDailyData(ctx context.Context, stockCode string, tradeDate time.Time) error
	UpsertDailyData(ctx context.Context, data *StockDailyData) error
	UpsertDailyDataBatch(ctx context.Context, data []StockDailyData) (int, error)

	// Stock operations
	GetStock(ctx context.Context, stockCode string) (*Stock, error)
	ListStocks(ctx context.Context, isActive bool) ([]Stock, error)
	CreateStock(ctx context.Context, stock *Stock) error
	UpdateStock(ctx context.Context, stock *Stock) error

	// TaskExecutionLog operations
	CreateTaskLog(ctx context.Context, log *TaskExecutionLog) (int64, error)
	UpdateTaskLog(ctx context.Context, log *TaskExecutionLog) error
	GetTaskLog(ctx context.Context, id int64) (*TaskExecutionLog, error)
	ListRecentTaskLogs(ctx context.Context, limit int) ([]TaskExecutionLog, error)

	// Utility operations
	CheckDataExists(ctx context.Context, stockCode string, tradeDate time.Time) (bool, error)
	GetDataQualityStats(ctx context.Context, stockCode string) (map[string]int, error)
	GetStocksSummary(ctx context.Context) ([]StockSummaryItem, error)
	Close() error
}

// StockSummaryItem 股票統計項目
type StockSummaryItem struct {
	StockCode   string  `db:"stock_code" json:"stock_code"`
	StockName   string  `db:"stock_name" json:"stock_name"`
	RecordCount int     `db:"record_count" json:"record_count"`
	LatestDate  *string `db:"latest_date" json:"latest_date"`
	FirstDate   *string `db:"first_date" json:"first_date"`
	DataSource  *string `db:"data_source" json:"data_source"`
}

// PostgresRepository implements the Repository interface using PostgreSQL
type PostgresRepository struct {
	db *PostgresDB
}

// NewPostgresRepository creates a new PostgreSQL repository
func NewPostgresRepository(db *PostgresDB) *PostgresRepository {
	return &PostgresRepository{
		db: db,
	}
}

// CreateDailyData inserts a new daily data record
func (r *PostgresRepository) CreateDailyData(ctx context.Context, data *StockDailyData) error {
	query := `
		INSERT INTO stock_daily_data (
			stock_code, trade_date, open_price, high_price, low_price, close_price,
			volume, turnover, data_source, data_quality, is_validated, created_at
		) VALUES (
			:stock_code, :trade_date, :open_price, :high_price, :low_price, :close_price,
			:volume, :turnover, :data_source, :data_quality, :is_validated, NOW()
		)
		RETURNING id, created_at
	`

	stmt, err := r.db.DB().PrepareNamedContext(ctx, query)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	if err := stmt.GetContext(ctx, data, data); err != nil {
		return fmt.Errorf("failed to insert daily data: %w", err)
	}

	return nil
}

// CreateDailyDataBatch inserts multiple daily data records in a transaction
func (r *PostgresRepository) CreateDailyDataBatch(ctx context.Context, data []StockDailyData) error {
	if len(data) == 0 {
		return nil
	}

	return r.db.WithTransaction(ctx, func(tx *sqlx.Tx) error {
		query := `
			INSERT INTO stock_daily_data (
				stock_code, trade_date, open_price, high_price, low_price, close_price,
				volume, turnover, data_source, data_quality, is_validated, created_at
			) VALUES (
				:stock_code, :trade_date, :open_price, :high_price, :low_price, :close_price,
				:volume, :turnover, :data_source, :data_quality, :is_validated, NOW()
			)
		`

		stmt, err := tx.PrepareNamedContext(ctx, query)
		if err != nil {
			return fmt.Errorf("failed to prepare statement: %w", err)
		}
		defer stmt.Close()

		for i := range data {
			if _, err := stmt.ExecContext(ctx, &data[i]); err != nil {
				return fmt.Errorf("failed to insert record %d: %w", i, err)
			}
		}

		return nil
	})
}

// GetDailyData retrieves a single daily data record
func (r *PostgresRepository) GetDailyData(ctx context.Context, stockCode string, tradeDate time.Time) (*StockDailyData, error) {
	var data StockDailyData
	query := `
		SELECT * FROM stock_daily_data
		WHERE stock_code = $1 AND trade_date = $2
	`

	if err := r.db.DB().GetContext(ctx, &data, query, stockCode, tradeDate); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get daily data: %w", err)
	}

	return &data, nil
}

// GetDailyDataRange retrieves daily data within a date range
func (r *PostgresRepository) GetDailyDataRange(ctx context.Context, stockCode string, startDate, endDate time.Time) ([]StockDailyData, error) {
	var data []StockDailyData
	query := `
		SELECT * FROM stock_daily_data
		WHERE stock_code = $1 AND trade_date BETWEEN $2 AND $3
		ORDER BY trade_date ASC
	`

	if err := r.db.DB().SelectContext(ctx, &data, query, stockCode, startDate, endDate); err != nil {
		return nil, fmt.Errorf("failed to get daily data range: %w", err)
	}

	return data, nil
}

// GetLatestDailyData retrieves the most recent daily data for a stock
func (r *PostgresRepository) GetLatestDailyData(ctx context.Context, stockCode string) (*StockDailyData, error) {
	var data StockDailyData
	query := `
		SELECT * FROM stock_daily_data
		WHERE stock_code = $1
		ORDER BY trade_date DESC
		LIMIT 1
	`

	if err := r.db.DB().GetContext(ctx, &data, query, stockCode); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get latest daily data: %w", err)
	}

	return &data, nil
}

// UpdateDailyData updates an existing daily data record
func (r *PostgresRepository) UpdateDailyData(ctx context.Context, data *StockDailyData) error {
	query := `
		UPDATE stock_daily_data
		SET open_price = :open_price, high_price = :high_price, low_price = :low_price,
			close_price = :close_price, volume = :volume, turnover = :turnover,
			data_source = :data_source, data_quality = :data_quality,
			is_validated = :is_validated, updated_at = NOW()
		WHERE stock_code = :stock_code AND trade_date = :trade_date
	`

	result, err := r.db.DB().NamedExecContext(ctx, query, data)
	if err != nil {
		return fmt.Errorf("failed to update daily data: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("no rows updated for stock_code=%s, trade_date=%s", data.StockCode, data.TradeDate)
	}

	return nil
}

// DeleteDailyData deletes a daily data record
func (r *PostgresRepository) DeleteDailyData(ctx context.Context, stockCode string, tradeDate time.Time) error {
	query := `DELETE FROM stock_daily_data WHERE stock_code = $1 AND trade_date = $2`

	result, err := r.db.DB().ExecContext(ctx, query, stockCode, tradeDate)
	if err != nil {
		return fmt.Errorf("failed to delete daily data: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("no rows deleted for stock_code=%s, trade_date=%s", stockCode, tradeDate)
	}

	return nil
}

// UpsertDailyData inserts or updates a daily data record
func (r *PostgresRepository) UpsertDailyData(ctx context.Context, data *StockDailyData) error {
	query := `
		INSERT INTO stock_daily_data (
			stock_code, trade_date, open_price, high_price, low_price, close_price,
			volume, turnover, data_source, data_quality, is_validated, created_at
		) VALUES (
			:stock_code, :trade_date, :open_price, :high_price, :low_price, :close_price,
			:volume, :turnover, :data_source, :data_quality, :is_validated, NOW()
		)
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
		RETURNING id
	`

	stmt, err := r.db.DB().PrepareNamedContext(ctx, query)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	if err := stmt.GetContext(ctx, &data.ID, data); err != nil {
		return fmt.Errorf("failed to upsert daily data: %w", err)
	}

	return nil
}

// UpsertDailyDataBatch performs batch upsert of daily data records
func (r *PostgresRepository) UpsertDailyDataBatch(ctx context.Context, data []StockDailyData) (int, error) {
	if len(data) == 0 {
		return 0, nil
	}

	affectedCount := 0

	err := r.db.WithTransaction(ctx, func(tx *sqlx.Tx) error {
		query := `
			INSERT INTO stock_daily_data (
				stock_code, trade_date, open_price, high_price, low_price, close_price,
				volume, turnover, data_source, data_quality, is_validated, created_at
			) VALUES (
				:stock_code, :trade_date, :open_price, :high_price, :low_price, :close_price,
				:volume, :turnover, :data_source, :data_quality, :is_validated, NOW()
			)
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
		`

		stmt, err := tx.PrepareNamedContext(ctx, query)
		if err != nil {
			return fmt.Errorf("failed to prepare statement: %w", err)
		}
		defer stmt.Close()

		for i := range data {
			result, err := stmt.ExecContext(ctx, &data[i])
			if err != nil {
				logger.Error("Failed to upsert record",
					zap.String("stock_code", data[i].StockCode),
					zap.Time("trade_date", data[i].TradeDate),
					zap.Error(err),
				)
				continue
			}

			rows, _ := result.RowsAffected()
			affectedCount += int(rows)
		}

		return nil
	})

	if err != nil {
		return affectedCount, fmt.Errorf("batch upsert failed: %w", err)
	}

	return affectedCount, nil
}

// GetStock retrieves stock information by stock code
func (r *PostgresRepository) GetStock(ctx context.Context, stockCode string) (*Stock, error) {
	var stock Stock
	query := `SELECT * FROM stocks WHERE stock_code = $1`

	if err := r.db.DB().GetContext(ctx, &stock, query, stockCode); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get stock: %w", err)
	}

	return &stock, nil
}

// ListStocks retrieves all stocks, optionally filtered by active status
func (r *PostgresRepository) ListStocks(ctx context.Context, isActive bool) ([]Stock, error) {
	var stocks []Stock
	query := `SELECT * FROM stocks WHERE is_active = $1 ORDER BY stock_code`

	if err := r.db.DB().SelectContext(ctx, &stocks, query, isActive); err != nil {
		return nil, fmt.Errorf("failed to list stocks: %w", err)
	}

	return stocks, nil
}

// CreateStock inserts a new stock record
func (r *PostgresRepository) CreateStock(ctx context.Context, stock *Stock) error {
	query := `
		INSERT INTO stocks (stock_code, stock_name, market, industry, is_active, created_at)
		VALUES (:stock_code, :stock_name, :market, :industry, :is_active, NOW())
		RETURNING id, created_at
	`

	stmt, err := r.db.DB().PrepareNamedContext(ctx, query)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	if err := stmt.GetContext(ctx, stock, stock); err != nil {
		return fmt.Errorf("failed to create stock: %w", err)
	}

	return nil
}

// UpdateStock updates an existing stock record
func (r *PostgresRepository) UpdateStock(ctx context.Context, stock *Stock) error {
	query := `
		UPDATE stocks
		SET stock_name = :stock_name, market = :market, industry = :industry,
			is_active = :is_active, updated_at = NOW()
		WHERE stock_code = :stock_code
	`

	result, err := r.db.DB().NamedExecContext(ctx, query, stock)
	if err != nil {
		return fmt.Errorf("failed to update stock: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("no rows updated for stock_code=%s", stock.StockCode)
	}

	return nil
}

// CreateTaskLog inserts a new task execution log
func (r *PostgresRepository) CreateTaskLog(ctx context.Context, log *TaskExecutionLog) (int64, error) {
	query := `
		INSERT INTO task_execution_logs (
			task_name, task_type, parameters, status, start_time, progress,
			processed_count, total_count, success_count, error_count, created_by
		) VALUES (
			:task_name, :task_type, :parameters, :status, :start_time, :progress,
			:processed_count, :total_count, :success_count, :error_count, :created_by
		)
		RETURNING id
	`

	stmt, err := r.db.DB().PrepareNamedContext(ctx, query)
	if err != nil {
		return 0, fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	var id int64
	if err := stmt.GetContext(ctx, &id, log); err != nil {
		return 0, fmt.Errorf("failed to create task log: %w", err)
	}

	return id, nil
}

// UpdateTaskLog updates an existing task execution log
func (r *PostgresRepository) UpdateTaskLog(ctx context.Context, log *TaskExecutionLog) error {
	query := `
		UPDATE task_execution_logs
		SET status = :status, end_time = :end_time, duration_seconds = :duration_seconds,
			progress = :progress, processed_count = :processed_count, total_count = :total_count,
			success_count = :success_count, error_count = :error_count,
			result_summary = :result_summary, error_message = :error_message
		WHERE id = :id
	`

	result, err := r.db.DB().NamedExecContext(ctx, query, log)
	if err != nil {
		return fmt.Errorf("failed to update task log: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("no rows updated for task_log id=%d", log.ID)
	}

	return nil
}

// GetTaskLog retrieves a task execution log by ID
func (r *PostgresRepository) GetTaskLog(ctx context.Context, id int64) (*TaskExecutionLog, error) {
	var log TaskExecutionLog
	query := `SELECT * FROM task_execution_logs WHERE id = $1`

	if err := r.db.DB().GetContext(ctx, &log, query, id); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get task log: %w", err)
	}

	return &log, nil
}

// ListRecentTaskLogs retrieves recent task execution logs
func (r *PostgresRepository) ListRecentTaskLogs(ctx context.Context, limit int) ([]TaskExecutionLog, error) {
	var logs []TaskExecutionLog
	query := `
		SELECT * FROM task_execution_logs
		ORDER BY start_time DESC
		LIMIT $1
	`

	if err := r.db.DB().SelectContext(ctx, &logs, query, limit); err != nil {
		return nil, fmt.Errorf("failed to list task logs: %w", err)
	}

	return logs, nil
}

// CheckDataExists checks if data exists for a given stock and date
func (r *PostgresRepository) CheckDataExists(ctx context.Context, stockCode string, tradeDate time.Time) (bool, error) {
	var count int
	query := `
		SELECT COUNT(*) FROM stock_daily_data
		WHERE stock_code = $1 AND trade_date = $2
	`

	if err := r.db.DB().GetContext(ctx, &count, query, stockCode, tradeDate); err != nil {
		return false, fmt.Errorf("failed to check data existence: %w", err)
	}

	return count > 0, nil
}

// GetDataQualityStats retrieves data quality statistics for a stock
func (r *PostgresRepository) GetDataQualityStats(ctx context.Context, stockCode string) (map[string]int, error) {
	type qualityCount struct {
		DataQuality string `db:"data_quality"`
		Count       int    `db:"count"`
	}

	var results []qualityCount
	query := `
		SELECT data_quality, COUNT(*) as count
		FROM stock_daily_data
		WHERE stock_code = $1
		GROUP BY data_quality
	`

	if err := r.db.DB().SelectContext(ctx, &results, query, stockCode); err != nil {
		return nil, fmt.Errorf("failed to get quality stats: %w", err)
	}

	stats := make(map[string]int)
	for _, r := range results {
		quality := r.DataQuality
		if quality == "" {
			quality = "unknown"
		}
		stats[quality] = r.Count
	}

	return stats, nil
}

// GetStocksSummary 獲取所有股票的統計資料
func (r *PostgresRepository) GetStocksSummary(ctx context.Context) ([]StockSummaryItem, error) {
	var summary []StockSummaryItem
	query := `
		SELECT 
			s.stock_code,
			s.stock_name,
			COALESCE(COUNT(sd.id), 0) as record_count,
			TO_CHAR(MAX(sd.trade_date), 'YYYY-MM-DD') as latest_date,
			TO_CHAR(MIN(sd.trade_date), 'YYYY-MM-DD') as first_date,
			MAX(sd.data_source) as data_source
		FROM stocks s
		LEFT JOIN stock_daily_data sd ON s.stock_code = sd.stock_code
		WHERE s.is_active = true
		GROUP BY s.stock_code, s.stock_name
		ORDER BY s.stock_code
	`

	if err := r.db.DB().SelectContext(ctx, &summary, query); err != nil {
		return nil, fmt.Errorf("failed to get stocks summary: %w", err)
	}

	logger.Info("Retrieved stocks summary",
		zap.Int("count", len(summary)),
	)

	return summary, nil
}

// Close closes the database connection
func (r *PostgresRepository) Close() error {
	return r.db.Close()
}
