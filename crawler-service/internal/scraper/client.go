package scraper

import (
	"context"
	"fmt"
	"time"

	"github.com/valyala/fasthttp"
)

// HTTPClient HTTP 客戶端封裝
type HTTPClient struct {
	client  *fasthttp.Client
	timeout time.Duration
	headers map[string]string
}

// NewHTTPClient 建立 HTTP 客戶端
func NewHTTPClient(timeout time.Duration) *HTTPClient {
	return &HTTPClient{
		client: &fasthttp.Client{
			MaxConnsPerHost:     1000,
			MaxIdleConnDuration: 10 * time.Second,
			ReadTimeout:         timeout,
			WriteTimeout:        timeout,
		},
		timeout: timeout,
		headers: map[string]string{
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
			"Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		},
	}
}

// Get 發送 GET 請求
func (c *HTTPClient) Get(ctx context.Context, url string) ([]byte, error) {
	req := fasthttp.AcquireRequest()
	resp := fasthttp.AcquireResponse()
	defer fasthttp.ReleaseRequest(req)
	defer fasthttp.ReleaseResponse(resp)

	// 設定請求
	req.SetRequestURI(url)
	req.Header.SetMethod("GET")
	for key, value := range c.headers {
		req.Header.Set(key, value)
	}

	// 發送請求（帶超時）
	err := c.client.DoTimeout(req, resp, c.timeout)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}

	// 檢查狀態碼
	statusCode := resp.StatusCode()
	if statusCode != 200 {
		return nil, fmt.Errorf("unexpected status code: %d", statusCode)
	}

	// 複製回應內容
	body := make([]byte, len(resp.Body()))
	copy(body, resp.Body())

	return body, nil
}

// GetWithRetry 發送 GET 請求（帶重試）
func (c *HTTPClient) GetWithRetry(ctx context.Context, url string, retryCount int) ([]byte, error) {
	var lastErr error

	for i := 0; i < retryCount; i++ {
		// 檢查 context 是否已取消
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}

		body, err := c.Get(ctx, url)
		if err == nil {
			return body, nil
		}

		lastErr = err

		// 如果不是最後一次重試，等待後再試
		if i < retryCount-1 {
			// 指數退避
			waitTime := time.Duration(i+1) * 2 * time.Second
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(waitTime):
			}
		}
	}

	return nil, fmt.Errorf("failed after %d retries: %w", retryCount, lastErr)
}
