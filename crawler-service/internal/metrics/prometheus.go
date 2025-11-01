package metrics

import (
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Metrics Prometheus 指標
type Metrics struct {
	// HTTP 請求指標
	HTTPRequestsTotal   *prometheus.CounterVec
	HTTPRequestDuration *prometheus.HistogramVec

	// 爬蟲指標
	CrawlerRequestsTotal      *prometheus.CounterVec
	CrawlerFetchRequestsTotal *prometheus.CounterVec
	CrawlerRequestDuration    *prometheus.HistogramVec
	CrawlerSuccessRate        prometheus.Gauge

	// 資料庫指標
	DBOperationDuration *prometheus.HistogramVec
	DBConnectionPoolSize prometheus.Gauge

	// Worker 指標
	WorkerPoolSize      prometheus.Gauge
	WorkerQueueSize     prometheus.Gauge
	WorkerTasksTotal    *prometheus.CounterVec
	WorkerTaskDuration  *prometheus.HistogramVec
}

// NewMetrics 創建 Metrics 實例
func NewMetrics() *Metrics {
	return &Metrics{
		// HTTP 請求指標
		HTTPRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of HTTP requests",
			},
			[]string{"method", "path", "status"},
		),
		HTTPRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_duration_seconds",
				Help:    "HTTP request duration in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"method", "path"},
		),

		// 爬蟲指標
		CrawlerRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "crawler_requests_total",
				Help: "Total number of crawler requests",
			},
			[]string{"symbol", "broker", "status"},
		),
		CrawlerFetchRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "crawler_fetch_requests_total",
				Help: "Total number of fetch requests to brokers",
			},
			[]string{"broker", "status"},
		),
		CrawlerRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "crawler_request_duration_seconds",
				Help:    "Crawler request duration in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"broker"},
		),
		CrawlerSuccessRate: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "crawler_success_rate",
				Help: "Crawler success rate (0-1)",
			},
		),

		// 資料庫指標
		DBOperationDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "db_operation_duration_seconds",
				Help:    "Database operation duration in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"operation"},
		),
		DBConnectionPoolSize: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "db_connection_pool_size",
				Help: "Number of connections in the database pool",
			},
		),

		// Worker 指標
		WorkerPoolSize: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "worker_pool_size",
				Help: "Number of workers in the pool",
			},
		),
		WorkerQueueSize: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "worker_queue_size",
				Help: "Number of tasks in the worker queue",
			},
		),
		WorkerTasksTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "worker_tasks_total",
				Help: "Total number of worker tasks",
			},
			[]string{"status"},
		),
		WorkerTaskDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "worker_task_duration_seconds",
				Help:    "Worker task duration in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"symbol"},
		),
	}
}

// RecordHTTPRequest 記錄 HTTP 請求
func (m *Metrics) RecordHTTPRequest(method, path string, statusCode int, duration time.Duration) {
	status := http.StatusText(statusCode)
	m.HTTPRequestsTotal.WithLabelValues(method, path, status).Inc()
	m.HTTPRequestDuration.WithLabelValues(method, path).Observe(duration.Seconds())
}

// RecordCrawlerRequest 記錄爬蟲請求
func (m *Metrics) RecordCrawlerRequest(symbol, broker string, success bool, duration time.Duration) {
	status := "success"
	if !success {
		status = "failure"
	}
	m.CrawlerRequestsTotal.WithLabelValues(symbol, broker, status).Inc()
	m.CrawlerRequestDuration.WithLabelValues(broker).Observe(duration.Seconds())
}

// RecordBrokerFetch 記錄券商爬取
func (m *Metrics) RecordBrokerFetch(broker string, success bool) {
	status := "success"
	if !success {
		status = "failure"
	}
	m.CrawlerFetchRequestsTotal.WithLabelValues(broker, status).Inc()
}

// RecordDBOperation 記錄資料庫操作
func (m *Metrics) RecordDBOperation(operation string, duration time.Duration) {
	m.DBOperationDuration.WithLabelValues(operation).Observe(duration.Seconds())
}

// UpdateDBConnectionPool 更新資料庫連線池大小
func (m *Metrics) UpdateDBConnectionPool(size float64) {
	m.DBConnectionPoolSize.Set(size)
}

// RecordWorkerTask 記錄 Worker 任務
func (m *Metrics) RecordWorkerTask(symbol string, success bool, duration time.Duration) {
	status := "success"
	if !success {
		status = "failure"
	}
	m.WorkerTasksTotal.WithLabelValues(status).Inc()
	m.WorkerTaskDuration.WithLabelValues(symbol).Observe(duration.Seconds())
}

// UpdateWorkerPoolStats 更新 Worker Pool 統計
func (m *Metrics) UpdateWorkerPoolStats(poolSize, queueSize float64) {
	m.WorkerPoolSize.Set(poolSize)
	m.WorkerQueueSize.Set(queueSize)
}

// Handler 返回 Prometheus HTTP 處理器
func (m *Metrics) Handler() http.Handler {
	return promhttp.Handler()
}
