package config

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/viper"
)

var globalConfig *Config

// Load 載入配置
func Load(configPath string) (*Config, error) {
	v := viper.New()

	// 設定配置檔案
	if configPath != "" {
		v.SetConfigFile(configPath)
	} else {
		v.SetConfigName("config")
		v.SetConfigType("yaml")
		v.AddConfigPath("./configs")
		v.AddConfigPath(".")
	}

	// 自動讀取環境變數
	v.AutomaticEnv()
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	// 讀取配置檔案
	if err := v.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// 配置檔案不存在，使用預設值
			fmt.Println("Config file not found, using defaults and environment variables")
		} else {
			return nil, fmt.Errorf("failed to read config file: %w", err)
		}
	}

	// 環境變數覆蓋
	bindEnvVars(v)

	// 解析配置
	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// 驗證配置
	if err := validate(&cfg); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	globalConfig = &cfg
	return &cfg, nil
}

// Get 獲取全域配置
func Get() *Config {
	if globalConfig == nil {
		panic("config not loaded")
	}
	return globalConfig
}

// bindEnvVars 綁定環境變數
func bindEnvVars(v *viper.Viper) {
	// 服務器
	v.BindEnv("server.port", "SERVER_PORT")
	v.BindEnv("server.host", "SERVER_HOST")

	// 資料庫
	v.BindEnv("database.url", "DATABASE_URL")
	v.BindEnv("database.host", "DB_HOST")
	v.BindEnv("database.port", "DB_PORT")
	v.BindEnv("database.user", "DB_USER")
	v.BindEnv("database.password", "DB_PASSWORD")
	v.BindEnv("database.database", "DB_NAME")
	v.BindEnv("database.sslmode", "DB_SSLMODE")
	v.BindEnv("database.pool_size", "DB_POOL_SIZE")
	v.BindEnv("database.max_idle", "DB_MAX_IDLE")
	v.BindEnv("database.max_open_conns", "DB_MAX_OPEN_CONNS")
	v.BindEnv("database.max_idle_conns", "DB_MAX_IDLE_CONNS")
	v.BindEnv("database.conn_max_lifetime", "DB_CONN_MAX_LIFETIME")
	v.BindEnv("database.conn_max_idle_time", "DB_CONN_MAX_IDLE_TIME")

	// 爬蟲
	v.BindEnv("crawler.max_workers", "MAX_WORKERS")
	v.BindEnv("crawler.batch_size", "BATCH_SIZE")
	v.BindEnv("crawler.request_timeout", "REQUEST_TIMEOUT")

	// 日誌
	v.BindEnv("logging.level", "LOG_LEVEL")
	v.BindEnv("logging.format", "LOG_FORMAT")
	v.BindEnv("logging.output", "LOG_OUTPUT")

	// 監控
	v.BindEnv("metrics.enabled", "ENABLE_METRICS")
	v.BindEnv("metrics.port", "METRICS_PORT")
}

// validate 驗證配置
func validate(cfg *Config) error {
	// 驗證服務器配置
	if cfg.Server.Port <= 0 || cfg.Server.Port > 65535 {
		return fmt.Errorf("invalid server port: %d", cfg.Server.Port)
	}

	// 驗證資料庫配置
	if cfg.Database.URL == "" {
		return fmt.Errorf("database URL is required")
	}

	// 驗證爬蟲配置
	if cfg.Crawler.MaxWorkers <= 0 {
		return fmt.Errorf("max_workers must be positive")
	}

	if len(cfg.Crawler.BrokerURLs) == 0 {
		return fmt.Errorf("broker_urls cannot be empty")
	}

	// 驗證日誌配置
	validLogLevels := map[string]bool{
		"debug": true,
		"info":  true,
		"warn":  true,
		"error": true,
	}
	if !validLogLevels[cfg.Logging.Level] {
		return fmt.Errorf("invalid log level: %s", cfg.Logging.Level)
	}

	return nil
}

// LoadFromEnv 從環境變數載入配置（用於容器化部署）
func LoadFromEnv() (*Config, error) {
	configPath := os.Getenv("CONFIG_PATH")
	return Load(configPath)
}
