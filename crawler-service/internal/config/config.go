package config

import (
	"time"
)

// Config 應用程式配置
type Config struct {
	Server   ServerConfig   `mapstructure:"server"`
	Database DatabaseConfig `mapstructure:"database"`
	Crawler  CrawlerConfig  `mapstructure:"crawler"`
	Logging  LoggingConfig  `mapstructure:"logging"`
	Metrics  MetricsConfig  `mapstructure:"metrics"`
	Redis    RedisConfig    `mapstructure:"redis"`
}

// ServerConfig 服務器配置
type ServerConfig struct {
	Port            int           `mapstructure:"port"`
	Host            string        `mapstructure:"host"`
	ReadTimeout     time.Duration `mapstructure:"read_timeout"`
	WriteTimeout    time.Duration `mapstructure:"write_timeout"`
	ShutdownTimeout time.Duration `mapstructure:"shutdown_timeout"`
	CORS            CORSConfig    `mapstructure:"cors"`
}

// CORSConfig CORS 配置
type CORSConfig struct {
	AllowedOrigins []string `mapstructure:"allowed_origins"`
	AllowedMethods []string `mapstructure:"allowed_methods"`
	AllowedHeaders []string `mapstructure:"allowed_headers"`
	MaxAge         int      `mapstructure:"max_age"`
}

// DatabaseConfig 資料庫配置
type DatabaseConfig struct {
	URL             string        `mapstructure:"url"`
	Host            string        `mapstructure:"host"`
	Port            int           `mapstructure:"port"`
	User            string        `mapstructure:"user"`
	Password        string        `mapstructure:"password"`
	Database        string        `mapstructure:"database"`
	SSLMode         string        `mapstructure:"sslmode"`
	PoolSize        int           `mapstructure:"pool_size"`
	MaxIdle         int           `mapstructure:"max_idle"`
	MaxOpenConns    int           `mapstructure:"max_open_conns"`
	MaxIdleConns    int           `mapstructure:"max_idle_conns"`
	MaxLifetime     time.Duration `mapstructure:"max_lifetime"`
	ConnMaxLifetime time.Duration `mapstructure:"conn_max_lifetime"`
	ConnMaxIdleTime time.Duration `mapstructure:"conn_max_idle_time"`
	ConnectTimeout  time.Duration `mapstructure:"connect_timeout"`
}

// CrawlerConfig 爬蟲配置
type CrawlerConfig struct {
	MaxWorkers      int           `mapstructure:"max_workers"`
	BatchSize       int           `mapstructure:"batch_size"`
	RequestTimeout  time.Duration `mapstructure:"request_timeout"`
	RetryCount      int           `mapstructure:"retry_count"`
	SmartSkipDays   int           `mapstructure:"smart_skip_days"`
	BrokerURLs      []string      `mapstructure:"broker_urls"`
}

// LoggingConfig 日誌配置
type LoggingConfig struct {
	Level    string `mapstructure:"level"`
	Format   string `mapstructure:"format"`
	Output   string `mapstructure:"output"`
	FilePath string `mapstructure:"file_path"`
}

// MetricsConfig 監控配置
type MetricsConfig struct {
	Enabled bool   `mapstructure:"enabled"`
	Port    int    `mapstructure:"port"`
	Path    string `mapstructure:"path"`
}

// RedisConfig Redis 配置
type RedisConfig struct {
	Enabled  bool   `mapstructure:"enabled"`
	URL      string `mapstructure:"url"`
	PoolSize int    `mapstructure:"pool_size"`
}

// GetServerAddr 獲取服務器地址
func (c *ServerConfig) GetServerAddr() string {
	return c.Host + ":" + string(rune(c.Port))
}

// GetDSN 獲取資料庫連線字串
func (c *DatabaseConfig) GetDSN() string {
	return c.URL
}
