package storage

import (
	"context"
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver
	"github.com/stock-analysis/crawler-service/pkg/logger"
)

// PostgresConfig holds database configuration
type PostgresConfig struct {
	Host            string
	Port            int
	User            string
	Password        string
	Database        string
	SSLMode         string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
}

// PostgresDB wraps sqlx.DB with additional functionality
type PostgresDB struct {
	db     *sqlx.DB
	config *PostgresConfig
}

// NewPostgresDB creates a new PostgreSQL database connection
func NewPostgresDB(config *PostgresConfig) (*PostgresDB, error) {
	// Build connection string
	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		config.Host,
		config.Port,
		config.User,
		config.Password,
		config.Database,
		config.SSLMode,
	)

	// Open database connection
	db, err := sqlx.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Set connection pool parameters
	db.SetMaxOpenConns(config.MaxOpenConns)
	db.SetMaxIdleConns(config.MaxIdleConns)
	db.SetConnMaxLifetime(config.ConnMaxLifetime)
	db.SetConnMaxIdleTime(config.ConnMaxIdleTime)

	// Verify connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	logger.Info("Database connection established",
		"host", config.Host,
		"port", config.Port,
		"database", config.Database,
		"max_open_conns", config.MaxOpenConns,
		"max_idle_conns", config.MaxIdleConns,
	)

	return &PostgresDB{
		db:     db,
		config: config,
	}, nil
}

// NewPostgresDBFromURL creates a new PostgreSQL database connection from URL
func NewPostgresDBFromURL(url string, maxOpenConns, maxIdleConns int) (*PostgresDB, error) {
	db, err := sqlx.Open("postgres", url)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Set connection pool parameters
	db.SetMaxOpenConns(maxOpenConns)
	db.SetMaxIdleConns(maxIdleConns)
	db.SetConnMaxLifetime(time.Hour)
	db.SetConnMaxIdleTime(10 * time.Minute)

	// Verify connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	logger.Info("Database connection established from URL",
		"max_open_conns", maxOpenConns,
		"max_idle_conns", maxIdleConns,
	)

	return &PostgresDB{
		db:     db,
		config: &PostgresConfig{},
	}, nil
}

// DB returns the underlying sqlx.DB instance
func (p *PostgresDB) DB() *sqlx.DB {
	return p.db
}

// Close closes the database connection
func (p *PostgresDB) Close() error {
	if p.db != nil {
		logger.Info("Closing database connection")
		return p.db.Close()
	}
	return nil
}

// Ping verifies the database connection is still alive
func (p *PostgresDB) Ping(ctx context.Context) error {
	return p.db.PingContext(ctx)
}

// BeginTx starts a new transaction
func (p *PostgresDB) BeginTx(ctx context.Context) (*sqlx.Tx, error) {
	return p.db.BeginTxx(ctx, nil)
}

// Stats returns database statistics
func (p *PostgresDB) Stats() map[string]interface{} {
	stats := p.db.Stats()
	return map[string]interface{}{
		"max_open_connections": stats.MaxOpenConnections,
		"open_connections":     stats.OpenConnections,
		"in_use":               stats.InUse,
		"idle":                 stats.Idle,
		"wait_count":           stats.WaitCount,
		"wait_duration":        stats.WaitDuration.String(),
		"max_idle_closed":      stats.MaxIdleClosed,
		"max_lifetime_closed":  stats.MaxLifetimeClosed,
	}
}

// HealthCheck performs a health check on the database
func (p *PostgresDB) HealthCheck(ctx context.Context) error {
	// Check if we can ping the database
	if err := p.Ping(ctx); err != nil {
		return fmt.Errorf("database ping failed: %w", err)
	}

	// Check if we can execute a simple query
	var result int
	query := "SELECT 1"
	if err := p.db.GetContext(ctx, &result, query); err != nil {
		return fmt.Errorf("database query failed: %w", err)
	}

	if result != 1 {
		return fmt.Errorf("unexpected query result: got %d, want 1", result)
	}

	return nil
}

// Exec executes a query without returning any rows
func (p *PostgresDB) Exec(ctx context.Context, query string, args ...interface{}) error {
	_, err := p.db.ExecContext(ctx, query, args...)
	return err
}

// Query executes a query that returns rows
func (p *PostgresDB) Query(ctx context.Context, dest interface{}, query string, args ...interface{}) error {
	return p.db.SelectContext(ctx, dest, query, args...)
}

// QueryRow executes a query that is expected to return at most one row
func (p *PostgresDB) QueryRow(ctx context.Context, dest interface{}, query string, args ...interface{}) error {
	return p.db.GetContext(ctx, dest, query, args...)
}

// WithTransaction executes a function within a database transaction
func (p *PostgresDB) WithTransaction(ctx context.Context, fn func(*sqlx.Tx) error) error {
	tx, err := p.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}

	// Ensure rollback on panic
	defer func() {
		if r := recover(); r != nil {
			_ = tx.Rollback()
			panic(r)
		}
	}()

	// Execute the function
	if err := fn(tx); err != nil {
		if rbErr := tx.Rollback(); rbErr != nil {
			logger.Error("Failed to rollback transaction", "error", rbErr)
		}
		return err
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}
