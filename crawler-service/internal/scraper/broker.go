package scraper

import (
	"context"
	"fmt"
	"time"

	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// BrokerManager 券商管理器
type BrokerManager struct {
	brokers    []Broker
	client     *HTTPClient
	parser     *Parser
	validator  *Validator
	retryCount int
}

// NewBrokerManager 建立券商管理器
func NewBrokerManager(brokerURLs []string, timeout time.Duration, retryCount int) *BrokerManager {
	client := NewHTTPClient(timeout)
	parser := NewParser()
	validator := NewValidator()

	// 建立所有券商實例
	var brokers []Broker
	for _, url := range brokerURLs {
		broker := NewGenericBroker(url, client, parser, validator)
		brokers = append(brokers, broker)
	}

	return &BrokerManager{
		brokers:    brokers,
		client:     client,
		parser:     parser,
		validator:  validator,
		retryCount: retryCount,
	}
}

// FetchWithFailover 使用輪詢策略獲取資料（第一個成功就返回）
func (bm *BrokerManager) FetchWithFailover(ctx context.Context, symbol string) (*FetchResult, error) {
	var lastErr error

	for _, broker := range bm.brokers {
		start := time.Now()

		logger.Debug("Fetching from broker",
			zap.String("broker", broker.Name()),
			zap.String("symbol", symbol),
		)

		data, err := broker.FetchDailyData(ctx, symbol)
		duration := time.Since(start)

		if err != nil {
			logger.Warn("Failed to fetch from broker",
				zap.String("broker", broker.Name()),
				zap.String("symbol", symbol),
				zap.Error(err),
			)
			lastErr = err
			continue // 嘗試下一個券商
		}

		// 成功獲取資料
		logger.Info("Successfully fetched from broker",
			zap.String("broker", broker.Name()),
			zap.String("symbol", symbol),
			zap.Int("records", len(data)),
			zap.Duration("duration", duration),
		)

		return &FetchResult{
			Symbol:      symbol,
			Data:        data,
			Source:      broker.Name(),
			Success:     true,
			Duration:    duration,
			RecordCount: len(data),
		}, nil
	}

	// 所有券商都失敗
	return nil, fmt.Errorf("failed to fetch from all brokers: %w", lastErr)
}

// FetchFromAll 從所有券商獲取資料（用於資料比對）
func (bm *BrokerManager) FetchFromAll(ctx context.Context, symbol string) []*FetchResult {
	var results []*FetchResult

	for _, broker := range bm.brokers {
		start := time.Now()

		data, err := broker.FetchDailyData(ctx, symbol)
		duration := time.Since(start)

		result := &FetchResult{
			Symbol:   symbol,
			Data:     data,
			Source:   broker.Name(),
			Duration: duration,
		}

		if err != nil {
			result.Success = false
			result.Error = err
		} else {
			result.Success = true
			result.RecordCount = len(data)
		}

		results = append(results, result)
	}

	return results
}

// HealthCheckAll 檢查所有券商健康狀態
func (bm *BrokerManager) HealthCheckAll(ctx context.Context) map[string]error {
	results := make(map[string]error)

	for _, broker := range bm.brokers {
		err := broker.HealthCheck(ctx)
		results[broker.Name()] = err
	}

	return results
}

// GenericBroker 通用券商實作
type GenericBroker struct {
	name      string
	baseURL   string
	client    *HTTPClient
	parser    *Parser
	validator *Validator
}

// NewGenericBroker 建立通用券商
func NewGenericBroker(baseURL string, client *HTTPClient, parser *Parser, validator *Validator) *GenericBroker {
	return &GenericBroker{
		name:      extractBrokerName(baseURL),
		baseURL:   baseURL,
		client:    client,
		parser:    parser,
		validator: validator,
	}
}

// FetchDailyData 獲取日線資料
func (b *GenericBroker) FetchDailyData(ctx context.Context, symbol string) ([]DailyData, error) {
	// 建構 URL
	url := b.buildURL(symbol)

	// 發送請求
	body, err := b.client.GetWithRetry(ctx, url, 3)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch data: %w", err)
	}

	// 解析資料
	data, err := b.parser.ParseBrokerResponse(string(body), symbol)
	if err != nil {
		return nil, fmt.Errorf("failed to parse data: %w", err)
	}

	// 驗證資料
	validData, _ := b.validator.ValidateBatch(data)

	// 設定資料來源
	for i := range validData {
		validData[i].DataSource = b.name
	}

	return validData, nil
}

// Name 券商名稱
func (b *GenericBroker) Name() string {
	return b.name
}

// HealthCheck 健康檢查
func (b *GenericBroker) HealthCheck(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	_, err := b.client.Get(ctx, b.baseURL)
	return err
}

// buildURL 建構券商 URL
func (b *GenericBroker) buildURL(symbol string) string {
	// 券商 URL 格式: base_url + path + query
	path := "/z/BCD/czkc1.djbcd"
	query := fmt.Sprintf("?a=%s&b=A&c=2880&E=1&ver=5", symbol)
	return b.baseURL + path + query
}

// extractBrokerName 從 URL 提取券商名稱
func extractBrokerName(baseURL string) string {
	// 從 URL 中提取主機名
	// 例如: http://fubon-ebrokerdj.fbs.com.tw/ -> fubon
	if len(baseURL) > 7 {
		host := baseURL[7:] // 移除 http://
		if idx := len(host); idx > 0 {
			if idx := 0; idx < len(host) {
				for i, c := range host {
					if c == '.' || c == '/' {
						return host[:i]
					}
				}
			}
		}
	}
	return "unknown"
}
