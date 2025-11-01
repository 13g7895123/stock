# Go 專案執行流程完整指南

## 目錄
- [專案概述](#專案概述)
- [專案結構](#專案結構)
- [核心組件](#核心組件)
- [程式啟動流程](#程式啟動流程)
- [資料爬取流程](#資料爬取流程)
- [資料儲存流程](#資料儲存流程)
- [部署方式](#部署方式)
- [開發流程](#開發流程)
- [測試流程](#測試流程)
- [監控與日誌](#監控與日誌)

---

## 專案概述

**crawler-service** 是使用 Go 語言開發的高效能台灣股票資料爬蟲服務。

### 技術優勢
- **高效能**：相比 Python 版本提升 10-20 倍處理速度
- **高併發**：支援 1000+ Goroutines 並發處理
- **低資源**：記憶體使用降低 60-80%
- **易部署**：單一執行檔，無依賴問題

### 主要功能
- 從 8 個券商網站爬取股票日線資料
- 使用輪詢策略（failover）確保資料獲取穩定性
- 批次插入資料（使用 PostgreSQL COPY 協議）
- 提供 RESTful API 服務
- 整合 Prometheus metrics 監控
- 支援健康檢查

---

## 專案結構

```
crawler-service/
├── cmd/                          # 應用程式入口
│   └── crawler/
│       └── main.go              # 主程式
├── internal/                     # 內部套件（不可被外部引用）
│   ├── config/                  # 配置管理
│   │   ├── config.go           # 配置結構定義
│   │   └── loader.go           # 配置載入邏輯
│   ├── scraper/                 # 爬蟲核心
│   │   ├── broker.go           # 券商管理器
│   │   ├── client.go           # HTTP 客戶端
│   │   ├── parser.go           # 資料解析器
│   │   ├── validator.go        # 資料驗證器
│   │   └── types.go            # 資料類型定義
│   ├── storage/                 # 資料儲存
│   │   ├── postgres.go         # PostgreSQL 連線管理
│   │   ├── repository.go       # 資料庫操作介面
│   │   ├── batch.go            # 批次操作（COPY 協議）
│   │   └── models.go           # 資料模型
│   ├── api/                     # API 處理器
│   │   ├── handlers/           # HTTP 處理函式
│   │   └── middleware/         # 中介軟體
│   ├── worker/                  # 併發處理
│   └── metrics/                 # 監控指標
├── pkg/                         # 公共套件（可被外部引用）
│   ├── logger/                 # 日誌系統
│   ├── errors/                 # 錯誤處理
│   └── httputil/               # HTTP 工具
├── configs/                     # 配置檔案
│   └── config.yaml             # 主配置檔
├── deployments/                 # 部署配置
│   ├── Dockerfile              # Docker 映像
│   ├── docker-compose.yml      # 容器編排
│   └── prometheus.yml          # 監控配置
├── tests/                       # 測試
│   ├── unit/                   # 單元測試
│   ├── integration/            # 整合測試
│   └── e2e/                    # 端對端測試
├── scripts/                     # 腳本工具
├── go.mod                       # Go 模組定義
├── go.sum                       # 依賴版本鎖定
├── Makefile                     # 建構工具
└── README.md                    # 專案說明
```

---

## 核心組件

### 1. 配置管理 (internal/config/)

**功能**：管理應用程式配置，支援環境變數覆蓋

**主要檔案**：
- `config.go` - 定義配置結構（Server, Database, Crawler, Logging, Metrics, Redis）
- `loader.go` - 載入配置邏輯，使用 Viper 支援 YAML 和環境變數

**配置項目**：
```yaml
server:        # 服務器配置（port: 8080）
database:      # 資料庫配置（PostgreSQL）
crawler:       # 爬蟲配置（並發數、批次大小、券商 URLs）
logging:       # 日誌配置（level, format, output）
metrics:       # 監控配置（Prometheus）
redis:         # Redis 快取（選配）
```

### 2. 爬蟲核心 (internal/scraper/)

**功能**：從券商網站爬取股票資料

**核心類別**：

#### BrokerManager (broker.go)
- 管理多個券商
- 提供輪詢策略（FetchWithFailover）
- 健康檢查所有券商

#### HTTPClient (client.go)
- 封裝 HTTP 請求
- 支援重試機制
- 超時控制

#### Parser (parser.go)
- 解析券商回應資料
- 轉換為標準格式

#### Validator (validator.go)
- 驗證資料有效性
- 資料品質評分

**券商列表**（8 個）：
1. fubon-ebrokerdj
2. justdata-moneydj
3. jdata-yuanta
4. moneydj-emega
5. djfubonholdingfund
6. sjmain-esunsec
7. kgieworld
8. newjust-masterlink

### 3. 資料儲存 (internal/storage/)

**功能**：管理資料庫連線和資料操作

**核心類別**：

#### PostgresDB (postgres.go)
- 管理資料庫連線池
- 提供交易支援
- 健康檢查

#### Repository (repository.go)
- 定義資料操作介面
- 實作 CRUD 操作
- 支援 Upsert（插入或更新）

#### BatchInserter (batch.go)
- 使用 PostgreSQL COPY 協議高速插入
- 批次 Upsert 操作
- 連線池統計

**效能優勢**：
- COPY 協議比普通 INSERT 快 10-100 倍
- 批次操作減少網路往返
- 連線池複用提升效率

### 4. 日誌系統 (pkg/logger/)

**功能**：統一日誌管理

**特性**：
- 使用 Uber Zap（高效能日誌庫）
- 支援 JSON 和 Console 格式
- 可配置日誌等級（debug, info, warn, error）
- 輸出到 stdout 或檔案

---

## 程式啟動流程

### 完整流程圖

```
啟動
  │
  ├─→ 1. 載入配置 (LoadFromEnv)
  │     ├─ 讀取環境變數
  │     ├─ 讀取 config.yaml
  │     └─ 驗證配置有效性
  │
  ├─→ 2. 初始化日誌 (logger.Init)
  │     ├─ 設定日誌等級
  │     ├─ 設定輸出格式
  │     └─ 設定輸出目標
  │
  ├─→ 3. 建立爬蟲管理器 (NewBrokerManager)
  │     ├─ 初始化 HTTP Client
  │     ├─ 初始化 Parser
  │     ├─ 初始化 Validator
  │     └─ 建立 8 個券商實例
  │
  ├─→ 4. 健康檢查券商 (HealthCheckAll)
  │     └─ 測試所有券商網站連線
  │
  ├─→ 5. 初始化資料庫連線 (NewPostgresDB)
  │     ├─ 建立連線池
  │     ├─ 設定連線參數
  │     └─ Ping 測試
  │
  ├─→ 6. 初始化 Repository (NewPostgresRepository)
  │     └─ 封裝資料庫操作
  │
  ├─→ 7. 初始化批次插入器 (NewBatchInserter)
  │     ├─ 建立 pgx 連線池
  │     └─ 設定批次大小
  │
  ├─→ 8. 測試爬取與儲存（示範）
  │     ├─ 爬取 2330（台積電）
  │     ├─ 儲存到資料庫
  │     └─ 驗證資料
  │
  ├─→ 9. 啟動 HTTP 服務器
  │     ├─ 註冊路由
  │     │   ├─ /health
  │     │   ├─ /api/v1/stocks/:symbol/daily
  │     │   └─ /metrics
  │     └─ 監聽 port 8080
  │
  └─→ 10. 等待終止信號 (SIGINT/SIGTERM)
        └─ 優雅關閉（Graceful Shutdown）
```

### 詳細步驟說明

#### 步驟 1：載入配置
```go
// cmd/crawler/main.go:26
cfg, err := config.LoadFromEnv()
```
- 從環境變數 `CONFIG_PATH` 讀取配置檔路徑
- 使用 Viper 讀取 YAML 配置
- 環境變數覆蓋檔案配置
- 驗證配置有效性

#### 步驟 2：初始化日誌
```go
// cmd/crawler/main.go:33
logger.Init(cfg.Logging.Level, cfg.Logging.Format, ...)
```
- 設定 Zap logger
- 配置輸出格式（JSON/Console）
- 設定日誌等級

#### 步驟 3：建立爬蟲管理器
```go
// cmd/crawler/main.go:50
brokerManager := scraper.NewBrokerManager(...)
```
- 建立 8 個券商實例
- 配置超時時間（30s）
- 配置重試次數（3 次）

#### 步驟 4：健康檢查券商
```go
// cmd/crawler/main.go:62
healthStatus := brokerManager.HealthCheckAll(ctx)
```
- 測試所有券商網站
- 記錄健康狀態
- 統計可用券商數量

#### 步驟 5-7：初始化資料庫
```go
// cmd/crawler/main.go:85-129
db, err := storage.NewPostgresDB(dbConfig)
repo := storage.NewPostgresRepository(db)
batchInserter, err := storage.NewBatchInserter(...)
```
- 建立 PostgreSQL 連線池
- 設定連線參數（max_conns, idle_conns, lifetime）
- 初始化 Repository 和 BatchInserter

#### 步驟 8：測試爬取與儲存
```go
// cmd/crawler/main.go:141-217
result, err := brokerManager.FetchWithFailover(ctx, "2330")
rowsAffected, err := batchInserter.BatchUpsertWithRetry(ctx, dbRecords, 3)
```
- 測試爬取台積電資料
- 批次儲存到資料庫
- 驗證儲存結果

#### 步驟 9：啟動 HTTP 服務器
```go
// cmd/crawler/main.go:220-248
srv := &http.Server{Addr: ":8080", Handler: mux}
go func() { srv.ListenAndServe() }()
```
- 註冊 HTTP 路由
- 啟動 Goroutine 監聽請求

#### 步驟 10：優雅關閉
```go
// cmd/crawler/main.go:251-265
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit
srv.Shutdown(shutdownCtx)
```
- 監聽終止信號
- 優雅關閉 HTTP 服務器
- 關閉資料庫連線

---

## 資料爬取流程

### 爬取流程圖

```
API 請求 /api/v1/stocks/2330/daily
  │
  ├─→ 1. BrokerManager.FetchWithFailover(ctx, "2330")
  │     │
  │     ├─→ 嘗試券商 1 (fubon)
  │     │   ├─ GenericBroker.FetchDailyData()
  │     │   │   ├─ buildURL("2330")
  │     │   │   ├─ HTTPClient.GetWithRetry(url, 3)
  │     │   │   │   ├─ 重試 1：成功 → 返回資料
  │     │   │   │   ├─ 重試 2：失敗
  │     │   │   │   └─ 重試 3：失敗
  │     │   │   ├─ Parser.ParseBrokerResponse(body)
  │     │   │   └─ Validator.ValidateBatch(data)
  │     │   └─ 返回結果
  │     │
  │     ├─→ 成功？→ 是：返回資料
  │     │
  │     ├─→ 否：嘗試券商 2 (moneydj)
  │     ├─→ 否：嘗試券商 3 (yuanta)
  │     └─→ ...直到成功或所有券商失敗
  │
  └─→ 2. 返回 FetchResult
        ├─ Symbol: "2330"
        ├─ Data: []DailyData
        ├─ Source: "fubon"
        ├─ Success: true
        ├─ Duration: 350ms
        └─ RecordCount: 180
```

### 爬取策略：輪詢 (Failover)

**優勢**：
- 第一個成功就返回，速度快
- 自動切換券商，容錯性高
- 每個券商支援 3 次重試

**重試邏輯**：
```
請求 → 超時/失敗 → 重試 1 → 失敗 → 重試 2 → 失敗 → 重試 3 → 失敗
                                                              ↓
                                                         切換下一個券商
```

### 資料格式

**券商回應 → Parser 解析 → 標準格式**

```go
type DailyData struct {
    StockCode    string    // 股票代碼 "2330"
    TradeDate    time.Time // 交易日期
    OpenPrice    float64   // 開盤價
    HighPrice    float64   // 最高價
    LowPrice     float64   // 最低價
    ClosePrice   float64   // 收盤價
    Volume       int64     // 成交量
    DataSource   string    // 資料來源 "fubon"
    DataQuality  string    // 資料品質 "good"
}
```

### Validator 驗證規則

1. **價格驗證**
   - 開盤價 > 0
   - 最高價 >= 最低價
   - 收盤價在合理範圍內

2. **成交量驗證**
   - 成交量 >= 0

3. **資料完整性**
   - 必要欄位不可為空

4. **品質評分**
   - `good` - 所有驗證通過
   - `warning` - 部分欄位異常但可用
   - `bad` - 驗證失敗

---

## 資料儲存流程

### 儲存流程圖

```
爬取結果 []DailyData
  │
  ├─→ 1. 轉換為資料庫模型
  │     └─ DailyData → StockDailyData
  │
  ├─→ 2. BatchInserter.BatchUpsertWithRetry(ctx, data, 3)
  │     │
  │     ├─→ 嘗試 1：BatchUpsertDailyData(data)
  │     │   │
  │     │   ├─→ 分批處理（每批 50 筆）
  │     │   │   ├─ batch 1: data[0:50]
  │     │   │   ├─ batch 2: data[50:100]
  │     │   │   └─ batch 3: data[100:150]
  │     │   │
  │     │   ├─→ batchUpsertChunk(batch)
  │     │   │   ├─ 建構 multi-row INSERT SQL
  │     │   │   ├─ ON CONFLICT (stock_code, trade_date) DO UPDATE
  │     │   │   └─ 執行 SQL
  │     │   │
  │     │   └─→ 累計 rowsAffected
  │     │
  │     ├─→ 成功？→ 是：返回結果
  │     │
  │     ├─→ 否：等待 1 秒，重試 2
  │     ├─→ 否：等待 2 秒，重試 3
  │     └─→ 失敗：返回錯誤
  │
  └─→ 3. 返回儲存結果
        └─ rowsAffected: 150
```

### 批次操作方式

#### 方式 1：COPY 協議（最快）
```go
BatchInsertDailyData(ctx, data)
```
- 使用 PostgreSQL COPY FROM STDIN
- 速度最快（10-100 倍於 INSERT）
- **限制**：不支援衝突處理（ON CONFLICT）
- **適用**：全新資料插入

#### 方式 2：批次 Upsert（常用）
```go
BatchUpsertDailyData(ctx, data)
```
- 使用 multi-row INSERT + ON CONFLICT
- 支援自動更新重複資料
- 批次大小：50 筆/批
- **適用**：日常資料更新

### Upsert SQL 邏輯

```sql
INSERT INTO stock_daily_data (
    stock_code, trade_date, open_price, ...
) VALUES
    ('2330', '2024-01-01', 580.0, ...),
    ('2330', '2024-01-02', 582.0, ...),
    ...
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    ...
    updated_at = NOW()
```

**說明**：
- 如果 (stock_code, trade_date) 已存在 → 更新
- 如果不存在 → 插入
- 自動維護 updated_at 時間戳

### 資料庫模型

```go
type StockDailyData struct {
    ID          int64      `db:"id"`
    StockCode   string     `db:"stock_code"`
    TradeDate   time.Time  `db:"trade_date"`
    OpenPrice   *float64   `db:"open_price"`
    HighPrice   *float64   `db:"high_price"`
    LowPrice    *float64   `db:"low_price"`
    ClosePrice  *float64   `db:"close_price"`
    Volume      *int64     `db:"volume"`
    Turnover    *float64   `db:"turnover"`
    DataSource  string     `db:"data_source"`
    DataQuality *string    `db:"data_quality"`
    IsValidated bool       `db:"is_validated"`
    CreatedAt   time.Time  `db:"created_at"`
    UpdatedAt   *time.Time `db:"updated_at"`
}
```

---

## 部署方式

### 方式 1：本機執行

#### 前置需求
- Go 1.21+
- PostgreSQL 15+
- Make（選配）

#### 步驟

1. **安裝依賴**
```bash
cd crawler-service
go mod download
```

2. **配置資料庫**
```bash
# 編輯配置檔
cp configs/config.yaml configs/config.local.yaml
vim configs/config.local.yaml
```

修改資料庫連線：
```yaml
database:
  url: "postgresql://stock_user:password@localhost:9221/stock_analysis"
```

3. **執行程式**
```bash
# 使用 Makefile
make run

# 或直接執行
go run ./cmd/crawler/main.go

# 或建構後執行
make build
./bin/crawler-service
```

4. **驗證服務**
```bash
# 健康檢查
curl http://localhost:8080/health

# 測試 API
curl http://localhost:8080/api/v1/stocks/2330/daily
```

### 方式 2：Docker 部署

#### 步驟

1. **建構 Docker 映像**
```bash
make docker-build
```

2. **執行容器**
```bash
make docker-run
```

3. **查看日誌**
```bash
make logs
```

4. **停止容器**
```bash
make docker-stop
```

### 方式 3：docker-compose 部署（推薦）

#### 優勢
- 一鍵啟動所有服務
- 包含 PostgreSQL、Redis、Prometheus、Grafana
- 自動設定網路和資料卷

#### 步驟

1. **啟動所有服務**
```bash
cd crawler-service
make docker-compose-up
```

2. **查看服務狀態**
```bash
docker-compose -f deployments/docker-compose.yml ps
```

3. **存取服務**
- 爬蟲服務：http://localhost:8080
- PostgreSQL：localhost:9221
- Redis：localhost:9321
- Prometheus：http://localhost:9090
- Grafana：http://localhost:3001

4. **停止所有服務**
```bash
make docker-compose-down
```

### 環境變數配置

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `SERVER_PORT` | 服務埠號 | 8080 |
| `DATABASE_URL` | 資料庫連線字串 | - |
| `LOG_LEVEL` | 日誌等級 | info |
| `LOG_FORMAT` | 日誌格式 | json |
| `MAX_WORKERS` | 最大併發數 | 100 |
| `BATCH_SIZE` | 批次大小 | 50 |
| `REQUEST_TIMEOUT` | 請求超時 | 30s |
| `SMART_SKIP_DAYS` | 智能跳過天數 | 1 |

---

## 開發流程

### 標準開發流程

```
需求分析
  ↓
設計 API/功能
  ↓
撰寫測試（TDD）
  ↓
實作功能
  ↓
執行測試
  ↓
程式碼檢查（Lint）
  ↓
提交程式碼
```

### 常用開發命令

```bash
# 1. 格式化程式碼
make fmt

# 2. 程式碼檢查
make lint
make vet

# 3. 執行測試
make test          # 所有測試
make test-unit     # 單元測試
make test-integration  # 整合測試

# 4. 產生測試覆蓋率
make test-coverage

# 5. 效能測試
make test-bench

# 6. 下載依賴
make deps

# 7. 清理建構檔案
make clean

# 8. 安裝開發工具
make install-tools
```

### 新增功能範例

**情境**：新增取得股票歷史資料的 API

#### 步驟 1：設計 API
```
GET /api/v1/stocks/:symbol/history?start=2024-01-01&end=2024-12-31
```

#### 步驟 2：撰寫測試
```go
// tests/unit/api/handlers/stock_handler_test.go
func TestGetStockHistory(t *testing.T) {
    // 測試邏輯
}
```

#### 步驟 3：實作功能
```go
// internal/api/handlers/stock.go
func (h *StockHandler) GetHistory(c *gin.Context) {
    symbol := c.Param("symbol")
    start := c.Query("start")
    end := c.Query("end")

    // 實作邏輯
}
```

#### 步驟 4：執行測試
```bash
make test
```

#### 步驟 5：提交程式碼
```bash
git add .
git commit -m "feat: add stock history API"
```

---

## 測試流程

### 測試類型

#### 1. 單元測試 (Unit Tests)
**目的**：測試單一函式或方法

**範例**：
```go
// tests/unit/scraper/parser_test.go
func TestParseStockData(t *testing.T) {
    parser := scraper.NewParser()
    data, err := parser.ParseBrokerResponse(mockHTML, "2330")

    assert.NoError(t, err)
    assert.Equal(t, "2330", data[0].StockCode)
}
```

**執行**：
```bash
make test-unit
```

#### 2. 整合測試 (Integration Tests)
**目的**：測試多個元件整合

**範例**：
```go
// tests/integration/storage_test.go
func TestDatabaseIntegration(t *testing.T) {
    // 測試資料庫連線、插入、查詢
}
```

**執行**：
```bash
make test-integration
```

#### 3. 端對端測試 (E2E Tests)
**目的**：測試完整業務流程

**範例**：
```go
// tests/e2e/crawl_and_save_test.go
func TestCrawlAndSave(t *testing.T) {
    // 1. 爬取資料
    // 2. 儲存資料
    // 3. 驗證資料
}
```

### 測試覆蓋率

```bash
# 產生覆蓋率報告
make test-coverage

# 查看 HTML 報告
open coverage.html
```

**目標覆蓋率**：
- 核心邏輯：> 80%
- 資料庫操作：> 70%
- API 處理器：> 70%

### Mock 測試

使用 `sqlmock` 模擬資料庫：

```go
func TestRepository(t *testing.T) {
    db, mock, err := sqlmock.New()
    require.NoError(t, err)
    defer db.Close()

    mock.ExpectQuery("SELECT .* FROM stock_daily_data").
        WillReturnRows(sqlmock.NewRows(columns).AddRow(...))

    // 測試邏輯
}
```

---

## 監控與日誌

### 日誌系統

**配置**：
```yaml
logging:
  level: "info"      # debug, info, warn, error
  format: "json"     # json, console
  output: "stdout"   # stdout, file
  file_path: "/var/log/crawler-service/app.log"
```

**使用範例**：
```go
import "github.com/stock-analysis/crawler-service/pkg/logger"

logger.Info("Starting crawler",
    zap.String("symbol", "2330"),
    zap.Int("workers", 100))

logger.Error("Failed to fetch data",
    zap.Error(err))
```

**日誌輸出**（JSON 格式）：
```json
{
  "level": "info",
  "ts": "2024-01-15T10:30:45.123Z",
  "msg": "Starting crawler",
  "symbol": "2330",
  "workers": 100
}
```

### Prometheus Metrics

**端點**：`http://localhost:8080/metrics`

**關鍵指標**：

| 指標名稱 | 類型 | 說明 |
|---------|------|------|
| `crawler_requests_total` | Counter | 總請求數 |
| `crawler_request_duration_seconds` | Histogram | 請求延遲 |
| `crawler_fetch_requests_total` | Counter | 爬蟲請求總數 |
| `crawler_success_rate` | Gauge | 成功率 |
| `db_operation_duration_seconds` | Histogram | 資料庫操作延遲 |
| `db_connection_pool_size` | Gauge | 連線池大小 |

**查詢範例**（PromQL）：
```promql
# 每秒請求數
rate(crawler_requests_total[5m])

# P95 延遲
histogram_quantile(0.95, rate(crawler_request_duration_seconds_bucket[5m]))

# 成功率
crawler_success_rate * 100
```

### Grafana 儀表板

**存取**：http://localhost:3001
- 帳號：admin
- 密碼：admin

**預設儀表板**：
1. 爬蟲效能監控
   - 請求數、成功率、延遲
2. 資料庫效能監控
   - 連線池狀態、查詢延遲
3. 系統資源監控
   - CPU、記憶體、Goroutine 數量

### 健康檢查

**端點**：
```bash
curl http://localhost:8080/health
```

**回應**：
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45Z",
  "components": {
    "database": "healthy",
    "brokers": "8/8 healthy"
  }
}
```

---

## 故障排查

### 常見問題

#### 1. 資料庫連線失敗
**錯誤**：`failed to connect to database`

**解決方案**：
```bash
# 檢查資料庫是否啟動
pg_isready -h localhost -p 9221

# 檢查連線字串
echo $DATABASE_URL

# 測試連線
psql "postgresql://stock_user:password@localhost:9221/stock_analysis"
```

#### 2. 記憶體使用過高
**解決方案**：
```yaml
# 調整 config.yaml
crawler:
  max_workers: 50  # 降低併發數
  batch_size: 25   # 降低批次大小
```

#### 3. 爬取失敗
**錯誤**：`failed to fetch from all brokers`

**排查步驟**：
```bash
# 1. 查看日誌
make logs

# 2. 測試券商網站
curl http://fubon-ebrokerdj.fbs.com.tw/

# 3. 檢查網路連線
ping fubon-ebrokerdj.fbs.com.tw
```

#### 4. Goroutine 洩漏
**排查**：
```bash
# 查看 Goroutine 數量（透過 pprof）
go tool pprof http://localhost:8080/debug/pprof/goroutine
```

### 日誌查看

```bash
# Docker 日誌
docker logs -f stock-crawler-go

# 本機日誌
tail -f /var/log/crawler-service/app.log

# 過濾錯誤日誌
docker logs stock-crawler-go 2>&1 | grep ERROR
```

---

## API 端點總覽

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/stocks/:symbol/daily` | 取得單一股票日線資料 |
| GET | `/api/v1/stocks/:symbol/history` | 查詢歷史資料 |
| POST | `/api/v1/stocks/batch-update` | 批次更新股票資料 |

---

## 效能指標

| 指標 | Python 版本 | Go 版本 | 提升倍數 |
|-----|-----------|---------|---------|
| 批次處理速度 | ~10 stocks/sec | 100-200 stocks/sec | 10-20x |
| 並發處理能力 | 4-8 threads | 1000+ goroutines | 100x+ |
| 記憶體使用 | ~500MB | ~100MB | 5x |
| Docker 映像大小 | ~500MB | ~20MB | 25x |
| 啟動時間 | ~5s | ~0.5s | 10x |

---

## 總結

### 核心優勢
1. **高效能**：Goroutine 併發 + COPY 協議批次插入
2. **高可用**：輪詢策略 + 自動重試 + 健康檢查
3. **易維護**：清晰的專案結構 + 完整的測試覆蓋
4. **易部署**：單一執行檔 + Docker 支援
5. **可觀測**：結構化日誌 + Prometheus metrics + Grafana 儀表板

### 最佳實踐
1. **開發**：遵循 TDD，先寫測試再實作
2. **測試**：維持高測試覆蓋率（> 70%）
3. **部署**：優先使用 docker-compose 部署
4. **監控**：定期查看 Grafana 儀表板
5. **日誌**：生產環境使用 JSON 格式日誌

### 下一步
1. 閱讀 [API 文檔](./crawler-service/docs/API.md)
2. 閱讀 [架構說明](./crawler-service/docs/ARCHITECTURE.md)
3. 查看 [Go 遷移計劃](./go-migration-plan.md)
4. 參與開發：提交 Issue 或 Pull Request

---

**文件版本**：v1.0.0
**更新日期**：2024-01-15
**維護者**：Stock Analysis Team
