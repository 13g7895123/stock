# Go 爬蟲服務遷移計劃

## 文檔資訊

- **版本**: v1.0
- **建立日期**: 2025-10-30
- **預計完成**: 4-6 週
- **負責人**: 開發團隊
- **狀態**: 計劃已核准，準備實施

---

## 執行摘要

### 專案目標

將現有 Python 爬蟲服務（8券商日線資料爬取）遷移至 **Go 獨立微服務**，保持與現有 Python API **完全相容**，預期效能提升 **10-20 倍**。

### 核心價值

1. **效能提升**: 利用 Go 的 Goroutine 實現真正的高並發，處理速度提升 10-20 倍
2. **資源節省**: 記憶體使用降低 60-80%，CPU 使用率降低 40-60%
3. **可維護性**: 靜態型別、編譯時檢查、單一執行檔部署
4. **可擴展性**: 為未來更多模組遷移建立技術基礎

### 關鍵決策

- **整合方式**: 獨立微服務（通過 HTTP API 與 Python 服務通訊）
- **實施時程**: 快速實施（4-6 週）
- **功能範圍**: 優先遷移 8 券商爬蟲核心功能
- **相容性**: 完全相容現有 Python API，前端無需改動

---

## 目錄

1. [背景分析](#背景分析)
2. [專案架構](#專案架構)
3. [技術選型](#技術選型)
4. [分階段實施計劃](#分階段實施計劃)
5. [整合方案](#整合方案)
6. [測試策略](#測試策略)
7. [部署策略](#部署策略)
8. [監控與告警](#監控與告警)
9. [風險評估](#風險評估)
10. [預期效益](#預期效益)

---

## 背景分析

### 現有系統分析

#### 爬蟲服務現況

**核心檔案**:
- `backend/src/services/daily_data_service.py` - 主要爬蟲服務
- `backend/src/services/concurrent_stock_updater.py` - 並發更新器
- `backend/src/services/optimized_batch_updater.py` - 優化批次更新器

**8個券商資料來源**:
```python
self.broker_urls = [
    "http://fubon-ebrokerdj.fbs.com.tw/",           # 富邦證券
    "http://justdata.moneydj.com.tw/",              # MoneyDJ
    "http://jdata.yuanta.com.tw/",                  # 元大證券
    "http://moneydj.emega.com.tw/",                 # 兆豐證券
    "http://djfubonholdingfund.fbs.com.tw/",       # 富邦投信
    "https://sjmain.esunsec.com.tw/",              # 玉山證券
    "http://kgieworld.moneydj.com/",               # 凱基證券
    "http://newjust.masterlink.com.tw/"            # 元富證券
]
```

**當前效能指標**:
- 並發數: 4-8 threads（受 Python GIL 限制）
- 單股處理時間: 30-120 秒
- 批次處理速度: ~10 stocks/second
- 記憶體使用: ~500MB
- CPU 使用率: 60-80%

### 效能瓶頸分析

#### 1. Python GIL 限制
- **問題**: Global Interpreter Lock 限制多執行緒 CPU 運算
- **影響**: ThreadPoolExecutor 無法充分利用多核 CPU
- **解決**: Go 原生支援真正的併發（Goroutines）

#### 2. 爬蟲併發能力不足
- **問題**: 最多 4-8 個併發連線
- **影響**: 1000+ 股票需要長時間處理
- **解決**: Go 可輕鬆支援 1000+ 併發 Goroutines

#### 3. 記憶體使用過高
- **問題**: Python 記憶體佔用大
- **影響**: 大批次處理時記憶體壓力大
- **解決**: Go 記憶體管理更高效

#### 4. 資料解析效能
- **問題**: Python 字串處理相對較慢
- **影響**: 大量資料解析耗時
- **解決**: Go 編譯型語言，執行速度快

### 為什麼選擇 Go？

| 特性 | Python | Go | 優勢 |
|-----|--------|-----|------|
| 併發模型 | Threading (GIL限制) | Goroutines (真併發) | ⭐⭐⭐⭐⭐ |
| 執行速度 | 解釋執行 | 編譯執行 | 10-50x |
| 記憶體使用 | 較高 | 較低 | 5-10x |
| 部署複雜度 | 需要依賴 | 單一執行檔 | ⭐⭐⭐⭐⭐ |
| 網路 I/O | 非同步 | 原生支援 | ⭐⭐⭐⭐⭐ |
| 學習曲線 | 簡單 | 中等 | ⭐⭐⭐ |
| 生態系統 | 豐富 | 成長中 | ⭐⭐⭐⭐ |

**結論**: 對於網路 I/O 密集、高併發的爬蟲服務，Go 是最佳選擇。

---

## 專案架構

### 整體架構圖

```
┌──────────────────────────────────────────────────────────┐
│                      前端應用                              │
│                  (Nuxt.js / Vue.js)                       │
└───────────────────────┬──────────────────────────────────┘
                        │ HTTP API
                        ▼
┌──────────────────────────────────────────────────────────┐
│                  Python Backend API                       │
│                  (FastAPI - Port 9121)                    │
│                                                            │
│  ┌──────────────────────────────────────────────┐        │
│  │      CrawlerClient (新增服務層)              │        │
│  │  - 智能路由（Go/Python）                     │        │
│  │  - 降級機制（Go失敗 → Python）               │        │
│  └───────────────┬──────────────────────────────┘        │
└──────────────────┼──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌─────────────┐      ┌──────────────────┐
│   Python    │      │   Go Crawler     │ 新建
│   Crawler   │      │   Service        │
│  (保留)     │      │  (Port 8080)     │
└─────┬───────┘      └────────┬─────────┘
      │                       │
      │    ┌──────────────────┘
      │    │
      ▼    ▼
┌─────────────────────────────────────┐
│        PostgreSQL Database           │
│         (Port 9221)                  │
│   - stock_daily_data                │
│   - stocks                           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         Redis Cache                  │
│         (Port 9321)                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    Prometheus + Grafana              │
│        監控系統                       │
└─────────────────────────────────────┘
```

### Go 專案目錄結構

```
crawler-service/
├── cmd/
│   └── crawler/
│       └── main.go                    # 服務入口點
│
├── internal/                          # 私有應用程式碼
│   ├── config/
│   │   ├── config.go                  # 配置結構定義
│   │   └── loader.go                  # 配置載入器
│   │
│   ├── scraper/                       # 爬蟲核心
│   │   ├── broker.go                  # 券商爬蟲介面
│   │   ├── broker_impl.go             # 8券商實作
│   │   ├── parser.go                  # 資料解析器
│   │   ├── validator.go               # 資料驗證器
│   │   ├── client.go                  # HTTP 客戶端封裝
│   │   └── types.go                   # 類型定義
│   │
│   ├── storage/                       # 資料儲存
│   │   ├── postgres.go                # PostgreSQL 操作
│   │   ├── repository.go              # Repository 介面
│   │   ├── batch.go                   # 批次操作
│   │   └── models.go                  # 資料庫模型
│   │
│   ├── worker/                        # 併發處理
│   │   ├── pool.go                    # Goroutine Pool
│   │   ├── batch_processor.go         # 批次處理器
│   │   └── task.go                    # 任務定義
│   │
│   ├── api/                           # API 處理器
│   │   ├── handlers/
│   │   │   ├── health.go              # 健康檢查
│   │   │   ├── stock.go               # 股票爬取 API
│   │   │   └── batch.go               # 批次更新 API
│   │   ├── middleware/
│   │   │   ├── logger.go              # 日誌中介軟體
│   │   │   ├── recovery.go            # 錯誤恢復
│   │   │   └── metrics.go             # 指標收集
│   │   └── router.go                  # 路由配置
│   │
│   └── metrics/                       # 監控指標
│       ├── prometheus.go              # Prometheus 整合
│       └── collector.go               # 自訂收集器
│
├── pkg/                               # 公共程式庫（可被外部使用）
│   ├── logger/
│   │   └── zap.go                     # 結構化日誌
│   ├── httputil/
│   │   └── client.go                  # HTTP 工具
│   └── errors/
│       └── errors.go                  # 錯誤處理
│
├── migrations/                        # 資料庫遷移（如需要）
│   └── 001_add_go_crawler_source.sql
│
├── tests/                             # 測試
│   ├── unit/                          # 單元測試
│   ├── integration/                   # 整合測試
│   └── e2e/                           # 端對端測試
│
├── deployments/                       # 部署配置
│   ├── Dockerfile                     # Docker 映像
│   ├── docker-compose.yml             # 本地部署
│   └── k8s/                           # Kubernetes 配置（選配）
│
├── scripts/                           # 工具腳本
│   ├── build.sh                       # 建構腳本
│   ├── test.sh                        # 測試腳本
│   └── deploy.sh                      # 部署腳本
│
├── configs/                           # 配置檔案
│   ├── config.yaml                    # 主配置
│   ├── config.dev.yaml                # 開發環境
│   └── config.prod.yaml               # 生產環境
│
├── docs/                              # 文檔
│   ├── API.md                         # API 文檔
│   ├── ARCHITECTURE.md                # 架構說明
│   └── DEVELOPMENT.md                 # 開發指南
│
├── go.mod                             # Go 模組定義
├── go.sum                             # 依賴版本鎖定
├── Makefile                           # 建構任務
└── README.md                          # 專案說明
```

### 核心模組說明

#### 1. Scraper（爬蟲核心）

**職責**: 從 8 個券商網站爬取股票日線資料

**核心介面**:
```go
type Broker interface {
    // 獲取股票日線資料
    FetchDailyData(ctx context.Context, symbol string) ([]DailyData, error)

    // 券商名稱
    Name() string

    // 健康檢查
    HealthCheck(ctx context.Context) error
}

type BrokerManager struct {
    brokers []Broker
    // 輪詢策略（第一個成功就返回）
    FetchWithFailover(ctx context.Context, symbol string) ([]DailyData, error)
}
```

#### 2. Storage（資料儲存）

**職責**: PostgreSQL 資料庫操作

**核心介面**:
```go
type Repository interface {
    // 儲存日線資料
    SaveDailyData(ctx context.Context, data []DailyData) error

    // 批次儲存（使用 COPY 協議）
    BatchSave(ctx context.Context, data []DailyData) error

    // 查詢最新日期
    GetLatestDate(ctx context.Context, symbol string) (time.Time, error)

    // 查詢歷史資料
    QueryHistory(ctx context.Context, symbol string, start, end time.Time) ([]DailyData, error)
}
```

#### 3. Worker（併發處理）

**職責**: 管理 Goroutine Pool，並發處理多個股票

**核心邏輯**:
```go
type BatchProcessor struct {
    pool       *ants.Pool      // Goroutine Pool
    db         Repository       // 資料庫
    scraper    *BrokerManager   // 爬蟲管理器
    maxWorkers int              // 最大併發數
}

// 批次更新股票
func (bp *BatchProcessor) UpdateBatch(ctx context.Context, symbols []string) (*Result, error) {
    // 使用 errgroup 管理併發任務
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(bp.maxWorkers)

    for _, symbol := range symbols {
        symbol := symbol  // 捕獲迴圈變數
        g.Go(func() error {
            return bp.updateSingle(ctx, symbol)
        })
    }

    return g.Wait()
}
```

#### 4. API（HTTP 服務）

**職責**: 提供 RESTful API，與 Python 服務完全相容

**路由設計**:
```go
// 與 Python API 完全相容的路由
router.GET("/api/v1/health", handlers.HealthCheck)
router.GET("/api/v1/stocks/:symbol/daily", handlers.FetchDaily)
router.POST("/api/v1/stocks/batch-update", handlers.BatchUpdate)
router.GET("/api/v1/stocks/:symbol/history", handlers.QueryHistory)
router.GET("/metrics", gin.WrapH(promhttp.Handler()))
```

---

## 技術選型

### 核心技術棧

#### Web 框架
- **選擇**: [Gin](https://github.com/gin-gonic/gin)
- **理由**:
  - 高效能（比其他 Go 框架快 40 倍）
  - 易用的 API
  - 中介軟體生態完整
  - 社群活躍

#### HTTP 客戶端
- **選擇**: [fasthttp](https://github.com/valyala/fasthttp) + `net/http`
- **理由**:
  - fasthttp: 極速（比 net/http 快 10 倍），用於爬蟲
  - net/http: 標準庫，穩定，用於其他 HTTP 呼叫

#### 資料庫
- **選擇**: [sqlx](https://github.com/jmoiron/sqlx) + [pgx](https://github.com/jackc/pgx)
- **理由**:
  - sqlx: 在標準庫基礎上擴展，易用
  - pgx: PostgreSQL 原生驅動，效能最佳
  - 支援 COPY 協議（批次插入極快）

#### 併發控制
- **Goroutine Pool**: [ants](https://github.com/panjf2000/ants)
- **錯誤處理**: [errgroup](https://pkg.go.dev/golang.org/x/sync/errgroup)
- **理由**:
  - ants: 高效能 Goroutine Pool，避免無限制創建 Goroutines
  - errgroup: 優雅處理併發錯誤

#### 配置管理
- **選擇**: [viper](https://github.com/spf13/viper)
- **理由**:
  - 支援多種配置格式（YAML、JSON、ENV）
  - 熱重載
  - 環境變數覆蓋

#### 日誌
- **選擇**: [zap](https://github.com/uber-go/zap)
- **理由**:
  - 結構化日誌
  - 極高效能（比其他日誌庫快 4-10 倍）
  - 支援多種輸出格式

#### 監控
- **選擇**: [Prometheus](https://prometheus.io/) + [Grafana](https://grafana.com/)
- **理由**:
  - 工業標準
  - 與 Go 整合完美
  - 豐富的儀表板

### 依賴套件清單

```go
// go.mod
module github.com/your-org/stock-crawler

go 1.21

require (
    // Web 框架
    github.com/gin-gonic/gin v1.9.1

    // HTTP 客戶端
    github.com/valyala/fasthttp v1.51.0

    // 資料庫
    github.com/jmoiron/sqlx v1.3.5
    github.com/jackc/pgx/v5 v5.5.0
    github.com/lib/pq v1.10.9

    // 併發控制
    github.com/panjf2000/ants/v2 v2.9.0
    golang.org/x/sync v0.5.0

    // 配置管理
    github.com/spf13/viper v1.18.1

    // 日誌
    go.uber.org/zap v1.26.0

    // 監控
    github.com/prometheus/client_golang v1.17.0

    // 測試
    github.com/stretchr/testify v1.8.4
    github.com/DATA-DOG/go-sqlmock v1.5.1

    // 工具
    github.com/google/uuid v1.5.0
)
```

---

## 分階段實施計劃

### 總體時程: 4-6 週

```
Week 1      Week 2      Week 3      Week 4      Week 5      Week 6
│           │           │           │           │           │
├───────────┤           │           │           │           │
│ 專案初始化 │           │           │           │           │
│ 核心爬蟲  │           │           │           │           │
└───────────┤           │           │           │           │
            ├───────────┤           │           │           │
            │ 資料庫整合 │           │           │           │
            │ 批次處理  │           │           │           │
            └───────────┤           │           │           │
                        ├───────────┤           │           │
                        │ API 服務  │           │           │
                        │ Python整合│           │           │
                        └───────────┤           │           │
                                    ├───────────┤           │
                                    │ 效能優化  │           │
                                    │ 監控建立  │           │
                                    └───────────┤           │
                                                ├───────────┤
                                                │ 部署測試  │
                                                │ 上線準備  │
                                                └───────────┤
                                                            ├───────────┐
                                                            │ 灰度發布  │
                                                            │ 穩定化    │
                                                            └───────────┘
```

### 第一週：專案初始化與核心爬蟲

#### 目標
建立專案架構，實作 8 券商爬取邏輯

#### 詳細任務

**Day 1-2: 專案初始化**
- [ ] 建立 `crawler-service/` 目錄結構
- [ ] 初始化 `go.mod`
- [ ] 安裝核心依賴套件
- [ ] 配置開發環境
- [ ] 建立 Makefile
- [ ] 建立基本配置檔案 (`config.yaml`)
- [ ] 實作配置載入器

**產出**:
```bash
crawler-service/
├── cmd/crawler/main.go
├── internal/config/
├── go.mod
├── go.sum
├── Makefile
└── configs/config.yaml
```

**Day 3-5: 核心爬蟲實作**
- [ ] 實作 HTTP 客戶端封裝（fasthttp）
- [ ] 實作 Broker 介面定義
- [ ] 實作 8 券商 URL 建構邏輯
- [ ] 實作資料解析器（支援券商回應格式）
- [ ] 實作錯誤處理與重試機制
- [ ] 實作輪詢策略（Failover）
- [ ] 實作超時控制

**產出**:
```go
// internal/scraper/broker.go
type Broker interface {
    FetchDailyData(ctx context.Context, symbol string) ([]DailyData, error)
    Name() string
    HealthCheck(ctx context.Context) error
}

// 8個券商的實作
type FubonBroker struct { ... }
type MoneyDJBroker struct { ... }
// ... 其他券商
```

**Day 6-7: 單元測試**
- [ ] 爬蟲邏輯測試
- [ ] 資料解析測試
- [ ] Mock HTTP 回應測試
- [ ] 錯誤處理測試

**交付標準**:
- ✅ 可獨立運行的爬蟲核心
- ✅ 單元測試覆蓋率 > 70%
- ✅ 基本 README 文檔
- ✅ 程式碼通過 `go vet` 和 `golint` 檢查

---

### 第二週：資料庫整合與批次處理

#### 目標
完成資料庫操作，實作批次更新功能

#### 詳細任務

**Day 1-3: PostgreSQL 整合**
- [ ] 資料庫連線池配置
- [ ] 定義 StockDailyData 模型
- [ ] 實作 Repository 介面
- [ ] 實作 CRUD 操作
- [ ] 實作批次插入（使用 pgx COPY）
- [ ] 實作批次更新（使用 ON CONFLICT）
- [ ] 資料庫事務處理

**產出**:
```go
// internal/storage/repository.go
type Repository interface {
    SaveDailyData(ctx context.Context, data []DailyData) error
    BatchSave(ctx context.Context, data []DailyData) error
    GetLatestDate(ctx context.Context, symbol string) (time.Time, error)
    QueryHistory(ctx context.Context, symbol string, start, end time.Time) ([]DailyData, error)
}
```

**Day 4-6: 並發批次處理**
- [ ] 實作 Goroutine Pool（ants）
- [ ] 實作並發控制（errgroup）
- [ ] 實作智能跳過機制（檢查最新日期）
- [ ] 實作進度追蹤
- [ ] 實作批次處理器

**產出**:
```go
// internal/worker/batch_processor.go
type BatchProcessor struct {
    pool    *ants.Pool
    db      Repository
    scraper *BrokerManager
}

func (bp *BatchProcessor) UpdateBatch(ctx context.Context, symbols []string) (*Result, error)
```

**Day 7: 資料驗證**
- [ ] 實作價格邏輯驗證（high >= low, open, close）
- [ ] 實作資料完整性檢查
- [ ] 實作資料品質標記
- [ ] 整合測試（資料庫 + 爬蟲）

**交付標準**:
- ✅ 完整的資料庫操作層
- ✅ 支援 1000+ 股票並發更新
- ✅ 整合測試通過
- ✅ 資料驗證機制完善

---

### 第三週：API 服務與 Python 整合

#### 目標
實作 HTTP API，確保與 Python 完全相容

#### 詳細任務

**Day 1-3: HTTP API 實作**
- [ ] 設定 Gin 框架
- [ ] 實作路由配置
- [ ] 實作 API Handlers
  - `GET /api/v1/health` - 健康檢查
  - `GET /api/v1/stocks/:symbol/daily` - 單股更新
  - `POST /api/v1/stocks/batch-update` - 批次更新
  - `GET /api/v1/stocks/:symbol/history` - 查詢歷史
- [ ] 實作中介軟體（日誌、錯誤恢復、CORS）
- [ ] 確保回應格式與 Python 完全一致

**產出**:
```go
// internal/api/handlers/stock.go
func FetchDaily(c *gin.Context) {
    symbol := c.Param("symbol")
    // ... 處理邏輯
    c.JSON(200, gin.H{
        "success": true,
        "message": "Data fetched successfully",
        "data": data,
        "updated_at": time.Now(),
    })
}
```

**Day 4-5: Python 服務整合**
- [ ] Python 端新增配置參數
  - `GO_CRAWLER_ENABLED`
  - `GO_CRAWLER_URL`
- [ ] Python 端實作 `CrawlerClient` 服務層
- [ ] 實作智能路由（Go/Python 選擇）
- [ ] 實作降級機制（Go 失敗時回退到 Python）
- [ ] 配置環境變數

**產出**:
```python
# backend/src/services/crawler_client.py
class CrawlerClient:
    def __init__(self):
        self.go_enabled = settings.GO_CRAWLER_ENABLED
        self.go_url = settings.GO_CRAWLER_URL

    def fetch_daily_data(self, symbol: str):
        if self.go_enabled:
            try:
                return self._fetch_from_go(symbol)
            except Exception as e:
                logger.warning(f"Go service failed, fallback to Python")
                return self._fetch_from_python(symbol)
        return self._fetch_from_python(symbol)
```

**Day 6-7: API 測試**
- [ ] 端對端測試
- [ ] 相容性測試（確保前端無感）
- [ ] 效能基準測試
- [ ] 壓力測試

**交付標準**:
- ✅ 完整的 RESTful API
- ✅ 與 Python 服務並行運作
- ✅ API 回應格式完全相容
- ✅ Swagger 文檔自動生成

---

### 第四週：效能優化與監控

#### 目標
效能調優，建立監控體系

#### 詳細任務

**Day 1-3: 效能優化**
- [ ] 連線池參數調優
- [ ] Goroutine Pool 大小調整
- [ ] HTTP 客戶端超時優化
- [ ] 記憶體使用優化
  - 使用 `sync.Pool` 複用物件
  - 避免不必要的記憶體分配
- [ ] 資料庫查詢優化
  - 批次操作最佳化
  - 索引檢查
- [ ] 效能分析（pprof）

**產出**:
```go
// 效能優化配置
MaxIdleConns:    100,
MaxOpenConns:    500,
MaxWorkers:      runtime.NumCPU() * 10,
BatchSize:       100,
ConnMaxLifetime: 5 * time.Minute,
```

**Day 4-5: 監控系統建立**
- [ ] Prometheus metrics 埋點
  - 請求總數、延遲、錯誤率
  - Goroutine 數量
  - 資料庫操作延遲
  - 爬蟲成功率
- [ ] Grafana 儀表板設計
  - 爬蟲效能總覽
  - 系統資源使用
  - 錯誤監控
- [ ] 結構化日誌（zap）
  - 日誌等級配置
  - 日誌輸出格式
  - 日誌輪轉

**產出**:
```go
// internal/metrics/prometheus.go
var (
    RequestTotal = prometheus.NewCounterVec(...)
    RequestDuration = prometheus.NewHistogramVec(...)
    CrawlerSuccessRate = prometheus.NewGaugeVec(...)
)
```

**Day 6-7: 效能測試**
- [ ] 壓力測試（1000 股票並發）
- [ ] 與 Python 效能對比測試
- [ ] 資源使用監控（CPU、記憶體、網路）
- [ ] 效能測試報告

**交付標準**:
- ✅ 效能提升 10-20 倍
- ✅ 完整監控體系運作
- ✅ 效能測試報告輸出
- ✅ 資源使用在預期範圍內

---

### 第五週：部署與上線準備

#### 目標
Docker 化部署，生產環境準備

#### 詳細任務

**Day 1-3: Docker 化**
- [ ] 撰寫 Dockerfile（多階段建構）
- [ ] 優化映像大小（使用 alpine）
- [ ] docker-compose.yml 整合
- [ ] 環境變數配置
- [ ] 健康檢查配置

**產出**:
```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o crawler-service ./cmd/crawler

FROM alpine:latest
COPY --from=builder /app/crawler-service /crawler-service
EXPOSE 8080
CMD ["/crawler-service"]
```

**Day 4-5: 部署測試**
- [ ] 本地 Docker 部署測試
- [ ] 與現有服務整合測試
- [ ] 資料一致性驗證
- [ ] 日誌收集測試
- [ ] 監控指標驗證

**Day 6-7: 上線準備**
- [ ] 撰寫部署文檔
  - 環境需求
  - 部署步驟
  - 配置說明
- [ ] 撰寫運維手冊
  - 常見問題排查
  - 日誌查看
  - 效能調優
- [ ] 撰寫回滾計劃
  - 回滾觸發條件
  - 回滾步驟
  - 資料恢復

**交付標準**:
- ✅ Docker 映像建構成功
- ✅ docker-compose 一鍵啟動
- ✅ 完整部署文檔
- ✅ 上線檢查清單完成

---

### 第六週：灰度發布與穩定化（選配）

#### 目標
逐步切換流量，確保穩定

#### 詳細任務

**Day 1-2: 灰度發布（5% 流量）**
- [ ] Python 端配置 5% 流量到 Go 服務
- [ ] 監控關鍵指標
  - 錯誤率
  - 回應延遲
  - 資料品質
  - 資源使用
- [ ] 日誌分析

**Day 3-4: 流量提升（5% → 50%）**
- [ ] 評估 5% 流量階段結果
- [ ] 逐步提升流量至 50%
- [ ] 持續監控
- [ ] 問題修復（如有）

**Day 5-6: 全量切換（50% → 100%）**
- [ ] 評估 50% 流量階段結果
- [ ] 切換至 100% 流量
- [ ] 密切監控 24 小時
- [ ] 效能數據收集

**Day 7: 穩定化與文檔**
- [ ] 確認系統穩定
- [ ] 更新文檔
- [ ] 團隊知識分享
- [ ] 後續優化計劃

**交付標準**:
- ✅ Go 服務承載 100% 爬蟲流量
- ✅ 穩定運行 1 週以上
- ✅ 無重大問題
- ✅ 達成效能目標

---

## 整合方案

### 架構模式：API Gateway

```
┌─────────────────────────────────────────────────────┐
│                   前端應用層                         │
│        無需改動，API 介面保持完全相容                │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/HTTPS
                   ▼
┌─────────────────────────────────────────────────────┐
│              Python Backend (FastAPI)                │
│                   Port: 9121                         │
│  ┌───────────────────────────────────────────────┐  │
│  │         CrawlerClient (新增服務層)            │  │
│  │  ┌─────────────────────────────────────────┐ │  │
│  │  │  1. 檢查 GO_CRAWLER_ENABLED 配置       │ │  │
│  │  │  2. 路由到 Go 或 Python 服務           │ │  │
│  │  │  3. 錯誤降級（Go失敗 → Python）        │ │  │
│  │  └─────────────────────────────────────────┘ │  │
│  └───────┬───────────────────────────────┬───────┘  │
└──────────┼───────────────────────────────┼──────────┘
           │                               │
      ┌────▼─────┐                  ┌──────▼──────┐
      │  Python  │                  │     Go      │
      │  Crawler │                  │  Crawler    │
      │  Service │                  │  Service    │
      │          │                  │ Port: 8080  │
      └────┬─────┘                  └──────┬──────┘
           │                               │
           └───────────┬───────────────────┘
                       │
              ┌────────▼─────────┐
              │   PostgreSQL DB  │
              │    Port: 9221    │
              └──────────────────┘
```

### Python 端實作

#### 1. 配置管理

```python
# backend/src/config/settings.py

class Settings(BaseSettings):
    # ... 現有配置 ...

    # Go 爬蟲服務配置
    GO_CRAWLER_ENABLED: bool = Field(
        default=False,
        env="GO_CRAWLER_ENABLED",
        description="是否啟用 Go 爬蟲服務"
    )

    GO_CRAWLER_URL: str = Field(
        default="http://localhost:8080",
        env="GO_CRAWLER_URL",
        description="Go 爬蟲服務 URL"
    )

    GO_CRAWLER_TIMEOUT: int = Field(
        default=30,
        env="GO_CRAWLER_TIMEOUT",
        description="Go 服務請求超時（秒）"
    )

    GO_CRAWLER_RETRY_COUNT: int = Field(
        default=3,
        env="GO_CRAWLER_RETRY_COUNT",
        description="Go 服務重試次數"
    )

    # 降級配置
    FALLBACK_TO_PYTHON: bool = Field(
        default=True,
        env="FALLBACK_TO_PYTHON",
        description="Go 失敗時是否降級到 Python"
    )

settings = Settings()
```

#### 2. 爬蟲客戶端

```python
# backend/src/services/crawler_client.py

import httpx
import logging
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class CrawlerClient:
    """統一的爬蟲服務客戶端，支援 Go/Python 路由"""

    def __init__(self):
        self.go_enabled = settings.GO_CRAWLER_ENABLED
        self.go_url = settings.GO_CRAWLER_URL
        self.timeout = settings.GO_CRAWLER_TIMEOUT
        self.fallback = settings.FALLBACK_TO_PYTHON

        # HTTP 客戶端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True
        )

    async def fetch_daily_data(
        self,
        symbol: str,
        force_python: bool = False
    ) -> Dict:
        """
        獲取股票日線資料

        Args:
            symbol: 股票代號
            force_python: 強制使用 Python 服務

        Returns:
            日線資料字典
        """
        # 強制使用 Python
        if force_python or not self.go_enabled:
            return await self._fetch_from_python(symbol)

        # 優先使用 Go 服務
        try:
            result = await self._fetch_from_go(symbol)
            logger.info(f"Successfully fetched {symbol} from Go service")
            return result
        except Exception as e:
            logger.warning(f"Go service failed for {symbol}: {e}")

            # 降級到 Python
            if self.fallback:
                logger.info(f"Falling back to Python service for {symbol}")
                return await self._fetch_from_python(symbol)
            else:
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _fetch_from_go(self, symbol: str) -> Dict:
        """從 Go 服務獲取資料"""
        url = f"{self.go_url}/api/v1/stocks/{symbol}/daily"

        response = await self.client.get(url)
        response.raise_for_status()

        data = response.json()

        # 驗證回應格式
        if not data.get("success"):
            raise ValueError(f"Go service returned error: {data.get('message')}")

        return data

    async def _fetch_from_python(self, symbol: str) -> Dict:
        """從 Python 服務獲取資料（現有實作）"""
        from .daily_data_service import DailyDataService

        service = DailyDataService(db_session=get_db())
        result = await service.get_daily_data_for_stock(symbol)

        return {
            "success": True,
            "message": "Data fetched from Python service",
            "data": result,
            "source": "python"
        }

    async def batch_update(
        self,
        symbols: Optional[List[str]] = None,
        force_python: bool = False
    ) -> Dict:
        """批次更新股票資料"""
        if force_python or not self.go_enabled:
            return await self._batch_update_python(symbols)

        try:
            result = await self._batch_update_go(symbols)
            logger.info(f"Batch update completed via Go service")
            return result
        except Exception as e:
            logger.warning(f"Go batch update failed: {e}")

            if self.fallback:
                logger.info("Falling back to Python batch update")
                return await self._batch_update_python(symbols)
            else:
                raise

    async def _batch_update_go(self, symbols: Optional[List[str]]) -> Dict:
        """Go 服務批次更新"""
        url = f"{self.go_url}/api/v1/stocks/batch-update"

        payload = {"symbols": symbols} if symbols else {}

        response = await self.client.post(url, json=payload, timeout=300)
        response.raise_for_status()

        return response.json()

    async def _batch_update_python(self, symbols: Optional[List[str]]) -> Dict:
        """Python 服務批次更新（現有實作）"""
        from .concurrent_stock_updater import ConcurrentStockUpdater

        updater = ConcurrentStockUpdater(get_db(), max_workers=4)
        result = await updater.update_stocks_concurrent(symbols)

        return {
            "success": True,
            "message": "Batch update completed via Python service",
            "result": result,
            "source": "python"
        }

    async def health_check(self) -> Dict:
        """健康檢查（包含 Go 服務）"""
        status = {
            "python": "healthy",
            "go": "unknown"
        }

        if self.go_enabled:
            try:
                url = f"{self.go_url}/api/v1/health"
                response = await self.client.get(url, timeout=5)

                if response.status_code == 200:
                    status["go"] = "healthy"
                else:
                    status["go"] = "unhealthy"
            except Exception as e:
                status["go"] = f"error: {str(e)}"
                logger.error(f"Go service health check failed: {e}")

        return status
```

#### 3. API 端點更新

```python
# backend/src/api/v1/endpoints/data.py

from fastapi import APIRouter, Depends, Query, Body
from typing import Optional, List
from ...services.crawler_client import CrawlerClient

router = APIRouter()

@router.get("/daily/{symbol}")
async def get_daily_data(
    symbol: str,
    force_python: bool = Query(False, description="強制使用 Python 服務"),
    client: CrawlerClient = Depends(get_crawler_client)
):
    """
    獲取股票日線資料

    - 優先使用 Go 服務（如果啟用）
    - Go 失敗時自動降級到 Python
    - 可強制使用 Python 服務
    """
    result = await client.fetch_daily_data(symbol, force_python=force_python)
    return result

@router.post("/batch-update")
async def batch_update_daily_data(
    symbols: Optional[List[str]] = Body(None),
    force_python: bool = Body(False),
    client: CrawlerClient = Depends(get_crawler_client)
):
    """批次更新股票日線資料"""
    result = await client.batch_update(symbols, force_python=force_python)
    return result

@router.get("/health")
async def crawler_health_check(
    client: CrawlerClient = Depends(get_crawler_client)
):
    """爬蟲服務健康檢查"""
    return await client.health_check()

# Dependency
def get_crawler_client() -> CrawlerClient:
    return CrawlerClient()
```

#### 4. 環境變數配置

```bash
# backend/.env

# Go 爬蟲服務配置
GO_CRAWLER_ENABLED=false          # 初始關閉，測試通過後開啟
GO_CRAWLER_URL=http://localhost:8080
GO_CRAWLER_TIMEOUT=30
GO_CRAWLER_RETRY_COUNT=3
FALLBACK_TO_PYTHON=true           # 啟用降級機制
```

### Go 端實作

#### API 完全相容保證

```go
// internal/api/handlers/stock.go

// Response 結構與 Python 完全一致
type DailyDataResponse struct {
    Success   bool        `json:"success"`
    Message   string      `json:"message"`
    Data      []StockData `json:"data"`
    UpdatedAt string      `json:"updated_at"`
    Source    string      `json:"source"` // 標記來源："go"
}

func FetchDaily(c *gin.Context) {
    symbol := c.Param("symbol")

    // 業務邏輯...
    data, err := scraper.FetchDailyData(c.Request.Context(), symbol)
    if err != nil {
        c.JSON(500, DailyDataResponse{
            Success: false,
            Message: err.Error(),
            Source:  "go",
        })
        return
    }

    c.JSON(200, DailyDataResponse{
        Success:   true,
        Message:   "Data fetched successfully",
        Data:      data,
        UpdatedAt: time.Now().Format(time.RFC3339),
        Source:    "go",
    })
}
```

### 整合測試

#### 相容性測試腳本

```python
# tests/integration/test_crawler_compatibility.py

import pytest
import httpx

class TestCrawlerCompatibility:
    """測試 Go 和 Python 爬蟲服務的相容性"""

    @pytest.mark.asyncio
    async def test_api_response_format(self):
        """測試 API 回應格式一致性"""
        symbol = "2330"

        # 從 Python 獲取
        python_resp = await fetch_from_python(symbol)

        # 從 Go 獲取
        go_resp = await fetch_from_go(symbol)

        # 驗證結構一致
        assert python_resp.keys() == go_resp.keys()
        assert python_resp["success"] == go_resp["success"]
        assert "data" in python_resp
        assert "data" in go_resp

    @pytest.mark.asyncio
    async def test_data_consistency(self):
        """測試資料一致性"""
        symbol = "2330"

        python_data = await fetch_from_python(symbol)
        go_data = await fetch_from_go(symbol)

        # 資料筆數應該相同
        assert len(python_data["data"]) == len(go_data["data"])

        # 價格資料應該一致
        for py_item, go_item in zip(python_data["data"], go_data["data"]):
            assert py_item["trade_date"] == go_item["trade_date"]
            assert abs(py_item["close_price"] - go_item["close_price"]) < 0.01
```

---

## 測試策略

### 測試金字塔

```
       ┌─────────────┐
       │     E2E     │  20%   端對端測試
       │    Tests    │
       ├─────────────┤
       │ Integration │  30%   整合測試
       │    Tests    │
       ├─────────────┤
       │    Unit     │  50%   單元測試
       │    Tests    │
       └─────────────┘
```

### 1. 單元測試（50%）

#### 目標覆蓋率：> 80%

#### 測試範圍

**Scraper 模組**:
```go
// tests/unit/scraper_test.go

func TestBrokerURLBuilder(t *testing.T) {
    broker := NewFubonBroker()
    url := broker.BuildURL("2330")
    assert.Contains(t, url, "2330")
    assert.Contains(t, url, "fubon-ebrokerdj.fbs.com.tw")
}

func TestDataParser(t *testing.T) {
    mockResponse := `106/05/02,106/05/03,...,244,244,...`
    data, err := ParseBrokerResponse(mockResponse, "2330")

    assert.NoError(t, err)
    assert.NotEmpty(t, data)
    assert.Equal(t, data[0].StockCode, "2330")
}

func TestDataValidator(t *testing.T) {
    invalidData := DailyData{
        HighPrice: 100,
        LowPrice:  110,  // 錯誤：低價 > 高價
    }

    err := Validate(invalidData)
    assert.Error(t, err)
}
```

**Storage 模組**:
```go
// tests/unit/storage_test.go

func TestBatchInsert(t *testing.T) {
    db, mock := NewMockDB()
    repo := NewRepository(db)

    // 準備測試資料
    data := []DailyData{ /* ... */ }

    // 設定 mock 期望
    mock.ExpectBegin()
    mock.ExpectExec("COPY stock_daily_data").WillReturnResult(sqlmock.NewResult(1, 100))
    mock.ExpectCommit()

    // 執行測試
    err := repo.BatchSave(context.Background(), data)
    assert.NoError(t, err)
    assert.NoError(t, mock.ExpectationsWereMet())
}
```

**Worker 模組**:
```go
// tests/unit/worker_test.go

func TestBatchProcessor(t *testing.T) {
    mockDB := NewMockRepository()
    mockScraper := NewMockScraper()

    processor := NewBatchProcessor(mockDB, mockScraper, 10)

    symbols := []string{"2330", "2317", "2454"}
    result, err := processor.UpdateBatch(context.Background(), symbols)

    assert.NoError(t, err)
    assert.Equal(t, 3, result.Processed)
    assert.Equal(t, 3, result.Success)
}
```

### 2. 整合測試（30%）

#### 測試範圍

**爬蟲 + 資料庫整合**:
```go
// tests/integration/scraper_storage_test.go

func TestScraperWithRealDatabase(t *testing.T) {
    // 使用測試資料庫
    db := setupTestDB(t)
    defer teardownTestDB(t, db)

    // 初始化服務
    scraper := NewBrokerManager(brokers)
    repo := NewRepository(db)

    // 爬取資料
    data, err := scraper.FetchWithFailover(context.Background(), "2330")
    require.NoError(t, err)

    // 儲存到資料庫
    err = repo.SaveDailyData(context.Background(), data)
    require.NoError(t, err)

    // 驗證資料已儲存
    saved, err := repo.QueryHistory(context.Background(), "2330", time.Now().AddDate(0, -1, 0), time.Now())
    require.NoError(t, err)
    assert.NotEmpty(t, saved)
}
```

**API + 完整流程**:
```go
// tests/integration/api_test.go

func TestAPIFetchDaily(t *testing.T) {
    // 啟動測試服務器
    router := setupRouter()
    server := httptest.NewServer(router)
    defer server.Close()

    // 發送請求
    resp, err := http.Get(server.URL + "/api/v1/stocks/2330/daily")
    require.NoError(t, err)
    defer resp.Body.Close()

    // 驗證回應
    assert.Equal(t, 200, resp.StatusCode)

    var result DailyDataResponse
    err = json.NewDecoder(resp.Body).Decode(&result)
    require.NoError(t, err)

    assert.True(t, result.Success)
    assert.NotEmpty(t, result.Data)
}
```

### 3. 端對端測試（20%）

#### 測試範圍

**與 Python 服務整合**:
```python
# tests/e2e/test_go_python_integration.py

class TestGoPythonIntegration:
    """端對端測試：Go 服務與 Python 服務整合"""

    def setup_method(self):
        """啟動 Go 和 Python 服務"""
        self.go_service = start_go_service()
        self.python_service = start_python_service()

    def teardown_method(self):
        """停止服務"""
        self.go_service.stop()
        self.python_service.stop()

    async def test_full_workflow(self):
        """測試完整工作流程"""
        # 1. 通過 Python API 觸發爬取（路由到 Go）
        response = await httpx.post(
            "http://localhost:9121/api/v1/stocks/batch-update",
            json={"symbols": ["2330", "2317"]}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # 2. 查詢資料（從資料庫）
        response = await httpx.get(
            "http://localhost:9121/api/v1/stocks/2330/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0

    async def test_fallback_mechanism(self):
        """測試降級機制"""
        # 1. 停止 Go 服務
        self.go_service.stop()

        # 2. 請求應該自動降級到 Python
        response = await httpx.get(
            "http://localhost:9121/api/v1/stocks/2330/daily"
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["source"] == "python"  # 確認來源
```

### 效能測試

#### 基準測試（Benchmark）

```go
// tests/benchmark/scraper_bench_test.go

func BenchmarkSingleStockFetch(b *testing.B) {
    scraper := NewBrokerManager(brokers)
    ctx := context.Background()

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = scraper.FetchWithFailover(ctx, "2330")
    }
}

func BenchmarkBatchUpdate100Stocks(b *testing.B) {
    processor := NewBatchProcessor(db, scraper, 100)
    symbols := generateSymbols(100)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = processor.UpdateBatch(context.Background(), symbols)
    }
}
```

#### 壓力測試

```bash
# 使用 vegeta 進行壓力測試

# 1. 準備目標
echo "GET http://localhost:8080/api/v1/stocks/2330/daily" | \
vegeta attack -duration=60s -rate=100 | \
vegeta report

# 2. 批次更新壓力測試
echo 'POST http://localhost:8080/api/v1/stocks/batch-update
Content-Type: application/json
@batch_payload.json' | \
vegeta attack -duration=120s -rate=10 | \
vegeta report --type=text
```

### 測試執行

#### Makefile 整合

```makefile
# Makefile

.PHONY: test
test: test-unit test-integration

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	go test -v -cover -race ./tests/unit/...

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	go test -v -tags=integration ./tests/integration/...

.PHONY: test-coverage
test-coverage:
	@echo "Generating coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

.PHONY: test-bench
test-bench:
	@echo "Running benchmarks..."
	go test -bench=. -benchmem ./tests/benchmark/...

.PHONY: test-e2e
test-e2e:
	@echo "Running E2E tests..."
	pytest tests/e2e/ -v
```

---

## 部署策略

### Docker 部署

#### 1. Dockerfile（多階段建構）

```dockerfile
# ==================== Stage 1: Builder ====================
FROM golang:1.21-alpine AS builder

# 安裝必要工具
RUN apk add --no-cache git make

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY go.mod go.sum ./

# 下載依賴
RUN go mod download

# 複製原始碼
COPY . .

# 建構應用程式
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o /crawler-service \
    ./cmd/crawler/main.go

# ==================== Stage 2: Runtime ====================
FROM alpine:latest

# 安裝 CA 證書（HTTPS 需要）
RUN apk --no-cache add ca-certificates tzdata

# 設定時區
ENV TZ=Asia/Taipei

# 建立非 root 使用者
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# 工作目錄
WORKDIR /app

# 從 builder 複製執行檔
COPY --from=builder /crawler-service /app/crawler-service

# 複製配置檔案
COPY configs/ /app/configs/

# 修改擁有者
RUN chown -R appuser:appuser /app

# 切換到非 root 使用者
USER appuser

# 暴露埠
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/v1/health || exit 1

# 啟動應用程式
ENTRYPOINT ["/app/crawler-service"]
```

**映像大小優化**:
- 使用 alpine 基底映像（~5MB）
- 多階段建構，分離建構和執行環境
- 靜態編譯（`CGO_ENABLED=0`）
- 使用 `-ldflags="-w -s"` 移除除錯資訊

**預期映像大小**: ~20MB（vs Python 映像 ~500MB）

#### 2. docker-compose.yml 整合

```yaml
version: '3.8'

services:
  # PostgreSQL 資料庫
  postgres:
    image: postgres:15-alpine
    container_name: stock-postgres
    restart: unless-stopped
    ports:
      - "9221:5432"
    environment:
      POSTGRES_DB: stock_analysis
      POSTGRES_USER: stock_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U stock_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: stock-redis
    restart: unless-stopped
    ports:
      - "9321:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Go 爬蟲服務（新增）
  crawler-service:
    build:
      context: ./crawler-service
      dockerfile: Dockerfile
    container_name: stock-crawler-go
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      # 資料庫配置
      DATABASE_URL: postgresql://stock_user:${DB_PASSWORD}@postgres:5432/stock_analysis
      DB_POOL_SIZE: 20
      DB_MAX_IDLE: 10
      DB_MAX_LIFETIME: 300s

      # 服務配置
      SERVER_PORT: 8080
      LOG_LEVEL: info
      LOG_FORMAT: json

      # 爬蟲配置
      MAX_WORKERS: 100
      BATCH_SIZE: 50
      REQUEST_TIMEOUT: 30s
      SMART_SKIP_DAYS: 1

      # 監控
      ENABLE_METRICS: "true"
      METRICS_PORT: 8080
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 128M

  # Python 後端
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: stock-backend
    restart: unless-stopped
    ports:
      - "9121:8000"
    environment:
      DATABASE_URL: postgresql://stock_user:${DB_PASSWORD}@postgres:5432/stock_analysis
      REDIS_URL: redis://redis:6379/0

      # Go 爬蟲整合
      GO_CRAWLER_ENABLED: "true"
      GO_CRAWLER_URL: http://crawler-service:8080
      GO_CRAWLER_TIMEOUT: 30
      FALLBACK_TO_PYTHON: "true"
    depends_on:
      - postgres
      - redis
      - crawler-service
    volumes:
      - ./backend:/app

  # Prometheus（監控）
  prometheus:
    image: prom/prometheus:latest
    container_name: stock-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./deployments/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana（視覺化）
  grafana:
    image: grafana/grafana:latest
    container_name: stock-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./deployments/grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

#### 3. Prometheus 配置

```yaml
# deployments/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Go 爬蟲服務
  - job_name: 'crawler-service'
    static_configs:
      - targets: ['crawler-service:8080']
    metrics_path: /metrics

  # Python 後端（如有 metrics）
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics

  # PostgreSQL Exporter（選配）
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 部署流程

#### 本地開發環境

```bash
# 1. 啟動所有服務
docker-compose up -d

# 2. 查看日誌
docker-compose logs -f crawler-service

# 3. 健康檢查
curl http://localhost:8080/api/v1/health
curl http://localhost:9121/api/v1/health

# 4. 測試爬取
curl http://localhost:9121/api/v1/stocks/2330/daily

# 5. 查看監控
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana
```

#### 生產環境部署

```bash
# 1. 建構映像
cd crawler-service
docker build -t stock-crawler:v1.0.0 .

# 2. 推送到映像倉庫（如使用私有倉庫）
docker tag stock-crawler:v1.0.0 registry.example.com/stock-crawler:v1.0.0
docker push registry.example.com/stock-crawler:v1.0.0

# 3. 部署到生產環境
# 使用 docker-compose
docker-compose -f docker-compose.prod.yml up -d

# 或使用 Kubernetes（見下方）
kubectl apply -f deployments/k8s/
```

### Kubernetes 部署（選配）

```yaml
# deployments/k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-service
  namespace: stock-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawler-service
  template:
    metadata:
      labels:
        app: crawler-service
    spec:
      containers:
      - name: crawler-service
        image: stock-crawler:v1.0.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: MAX_WORKERS
          value: "100"
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: crawler-service
  namespace: stock-system
spec:
  selector:
    app: crawler-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: crawler-service-hpa
  namespace: stock-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: crawler-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 監控與告警

### Prometheus Metrics

#### 關鍵指標定義

```go
// internal/metrics/prometheus.go

var (
    // 請求指標
    RequestTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "crawler_requests_total",
            Help: "Total number of crawler requests",
        },
        []string{"method", "endpoint", "status"},
    )

    RequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "crawler_request_duration_seconds",
            Help:    "Crawler request duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "endpoint"},
    )

    // 爬蟲指標
    CrawlerRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "crawler_fetch_requests_total",
            Help: "Total number of crawler fetch requests",
        },
        []string{"broker", "symbol", "status"},
    )

    CrawlerDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "crawler_fetch_duration_seconds",
            Help:    "Time spent fetching data from brokers",
            Buckets: []float64{.1, .5, 1, 2, 5, 10, 30},
        },
        []string{"broker"},
    )

    CrawlerSuccessRate = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "crawler_success_rate",
            Help: "Success rate of crawler requests (0-1)",
        },
        []string{"broker"},
    )

    // 資料庫指標
    DBOperationDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "db_operation_duration_seconds",
            Help:    "Database operation duration",
            Buckets: []float64{.001, .005, .01, .05, .1, .5, 1},
        },
        []string{"operation"},
    )

    DBConnectionsTotal = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "db_connections_total",
            Help: "Total number of database connections",
        },
    )

    DBConnectionsIdle = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "db_connections_idle",
            Help: "Number of idle database connections",
        },
    )

    // Goroutine 指標
    ActiveGoroutines = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "crawler_active_goroutines",
            Help: "Number of active goroutines",
        },
    )

    // 批次處理指標
    BatchProcessedTotal = prometheus.NewCounter(
        prometheus.CounterOpts{
            Name: "batch_processed_total",
            Help: "Total number of stocks processed in batches",
        },
    )

    BatchDuration = prometheus.NewHistogram(
        prometheus.HistogramOpts{
            Name:    "batch_duration_seconds",
            Help:    "Batch processing duration",
            Buckets: []float64{10, 30, 60, 120, 300, 600},
        },
    )
)

func init() {
    // 註冊所有指標
    prometheus.MustRegister(
        RequestTotal,
        RequestDuration,
        CrawlerRequestsTotal,
        CrawlerDuration,
        CrawlerSuccessRate,
        DBOperationDuration,
        DBConnectionsTotal,
        DBConnectionsIdle,
        ActiveGoroutines,
        BatchProcessedTotal,
        BatchDuration,
    )
}

// 定期更新 runtime 指標
func UpdateRuntimeMetrics() {
    ticker := time.NewTicker(10 * time.Second)
    for range ticker.C {
        ActiveGoroutines.Set(float64(runtime.NumGoroutine()))
    }
}
```

#### 使用範例

```go
// 記錄請求
func (h *Handler) FetchDaily(c *gin.Context) {
    start := time.Now()

    // 業務邏輯...

    // 記錄指標
    metrics.RequestTotal.WithLabelValues("GET", "/stocks/:symbol/daily", "200").Inc()
    metrics.RequestDuration.WithLabelValues("GET", "/stocks/:symbol/daily").Observe(time.Since(start).Seconds())
}

// 記錄爬蟲請求
func (b *Broker) Fetch(ctx context.Context, symbol string) error {
    start := time.Now()

    err := b.doFetch(ctx, symbol)

    status := "success"
    if err != nil {
        status = "error"
    }

    metrics.CrawlerRequestsTotal.WithLabelValues(b.Name(), symbol, status).Inc()
    metrics.CrawlerDuration.WithLabelValues(b.Name()).Observe(time.Since(start).Seconds())

    return err
}
```

### Grafana 儀表板

#### 1. 爬蟲效能總覽

**面板包含**:
- 總請求數（QPS）
- 平均回應時間
- 錯誤率
- 各券商成功率
- 活躍 Goroutine 數量

#### 2. 系統資源

**面板包含**:
- CPU 使用率
- 記憶體使用
- 網路 I/O
- 磁碟 I/O

#### 3. 資料庫效能

**面板包含**:
- 查詢延遲
- 連線池使用率
- 慢查詢
- 死鎖

#### 4. 業務指標

**面板包含**:
- 每日爬取股票數
- 資料更新延遲
- 資料品質評分

### 日誌系統

#### 結構化日誌

```go
// pkg/logger/zap.go

var log *zap.Logger

func Init(level string, format string) {
    var config zap.Config

    if format == "json" {
        config = zap.NewProductionConfig()
    } else {
        config = zap.NewDevelopmentConfig()
    }

    // 設定日誌等級
    config.Level = zap.NewAtomicLevelAt(getLogLevel(level))

    // 初始化
    var err error
    log, err = config.Build()
    if err != nil {
        panic(err)
    }
}

func Info(msg string, fields ...zap.Field) {
    log.Info(msg, fields...)
}

func Error(msg string, fields ...zap.Field) {
    log.Error(msg, fields...)
}

// 使用範例
logger.Info("Fetching stock data",
    zap.String("symbol", "2330"),
    zap.String("broker", "fubon"),
    zap.Duration("duration", time.Since(start)),
)
```

#### 日誌輸出格式

```json
{
  "level": "info",
  "ts": 1699000000.123,
  "caller": "scraper/broker.go:45",
  "msg": "Fetching stock data",
  "symbol": "2330",
  "broker": "fubon",
  "duration": "1.234s"
}
```

### 告警規則

```yaml
# deployments/prometheus/alerts.yml

groups:
  - name: crawler_alerts
    interval: 30s
    rules:
      # 錯誤率過高
      - alert: HighErrorRate
        expr: rate(crawler_requests_total{status="error"}[5m]) / rate(crawler_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for 5 minutes"

      # 回應時間過長
      - alert: SlowResponse
        expr: histogram_quantile(0.95, rate(crawler_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time"
          description: "95th percentile response time > 10s"

      # Goroutine 洩漏
      - alert: GoroutineLeek
        expr: crawler_active_goroutines > 10000
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Possible goroutine leak"
          description: "Too many active goroutines (>10000)"

      # 資料庫連線耗盡
      - alert: DBConnectionExhausted
        expr: db_connections_idle / db_connections_total < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
          description: "Less than 10% idle connections"
```

---

## 風險評估

### 風險矩陣

| 風險 | 機率 | 影響 | 等級 | 應對策略 |
|-----|------|------|------|---------|
| API 不相容導致前端異常 | 中 | 高 | 🔴 高 | 完整相容性測試 + 金絲雀發布 |
| Go 服務不穩定 | 中 | 高 | 🔴 高 | 降級機制 + 監控告警 |
| 資料不一致 | 低 | 高 | 🟡 中 | 資料驗證 + 雙寫驗證期 |
| 效能不如預期 | 低 | 中 | 🟡 中 | 效能基準測試 + 預留優化時間 |
| 券商網站格式變化 | 中 | 中 | 🟡 中 | 多資料源 + 告警 |
| 部署失敗 | 低 | 中 | 🟢 低 | 詳細部署文檔 + 回滾計劃 |

### 風險詳情與應對

#### 風險 1: API 不相容導致前端異常

**描述**: Go 服務的 API 回應格式與 Python 不完全一致，導致前端解析錯誤或功能異常。

**機率**: 中（如果測試不充分）

**影響**: 高（直接影響使用者體驗）

**應對策略**:
1. **預防**:
   - 在開發階段嚴格遵循 Python API 規範
   - 使用 JSON Schema 驗證回應格式
   - 撰寫詳細的相容性測試

2. **檢測**:
   - 端對端測試覆蓋所有 API 端點
   - 金絲雀發布（先切換 5% 流量觀察）
   - 監控前端錯誤率

3. **恢復**:
   - 快速回滾機制（1 分鐘內切回 Python）
   - 保留 Python 服務作為備份

**驗收標準**:
- ✅ 相容性測試全部通過
- ✅ 前端無需修改任何程式碼
- ✅ API 回應格式一致性 100%

---

#### 風險 2: Go 服務不穩定

**描述**: Go 服務在生產環境出現崩潰、記憶體洩漏、Goroutine 洩漏等問題。

**機率**: 中（新服務上線初期）

**影響**: 高（影響爬蟲功能）

**應對策略**:
1. **預防**:
   - 充分的壓力測試和穩定性測試
   - 使用 `context` 控制 Goroutine 生命週期
   - 實作 panic recovery 中介軟體
   - 設定資源限制（記憶體、Goroutine 數量）

2. **檢測**:
   - 健康檢查端點
   - Goroutine 數量監控
   - 記憶體使用監控
   - 錯誤率告警

3. **恢復**:
   - 自動降級到 Python 服務
   - Docker/K8s 自動重啟
   - 快速回滾流程

**驗收標準**:
- ✅ 穩定運行 1 週無重啟
- ✅ 記憶體使用穩定
- ✅ Goroutine 數量正常

---

#### 風險 3: 資料不一致

**描述**: Go 服務爬取的資料與 Python 服務不一致，或資料品質問題。

**機率**: 低（有多資料源驗證）

**影響**: 高（影響資料可信度）

**應對策略**:
1. **預防**:
   - 使用與 Python 相同的資料解析邏輯
   - 實作嚴格的資料驗證
   - 雙寫驗證期（Go 和 Python 同時爬取，比對結果）

2. **檢測**:
   - 資料一致性檢查任務
   - 異常資料告警
   - 定期與 Python 服務比對

3. **恢復**:
   - 發現不一致時立即告警
   - 標記問題資料
   - 必要時重新爬取

**驗收標準**:
- ✅ 資料一致性 > 99.9%
- ✅ 無重大資料品質問題

---

#### 風險 4: 效能不如預期

**描述**: Go 服務效能提升未達到 10 倍目標，或反而變慢。

**機率**: 低（Go 效能優勢明顯）

**影響**: 中（影響專案價值）

**應對策略**:
1. **預防**:
   - 提前進行效能基準測試
   - 使用 pprof 分析瓶頸
   - 預留效能優化時間（第四週）

2. **檢測**:
   - 效能監控儀表板
   - 與 Python 服務對比
   - 定期效能測試

3. **優化**:
   - CPU 和記憶體分析
   - 連線池調優
   - Goroutine 數量調整
   - 批次大小優化

**驗收標準**:
- ✅ 單股爬取速度提升 > 3 倍
- ✅ 批次處理速度提升 > 10 倍

---

## 預期效益

### 效能提升

| 指標 | Python 現況 | Go 目標 | 提升倍數 |
|-----|------------|---------|---------|
| **單股爬取時間** | 30-120 秒 | 5-20 秒 | **3-6x** |
| **批次處理速度** | ~10 stocks/sec | 100-200 stocks/sec | **10-20x** |
| **並發處理能力** | 4-8 threads | 1000+ goroutines | **100x+** |
| **記憶體使用** | ~500MB | ~100MB | **5x** |
| **CPU 使用率** | 60-80% | 30-50% | **更高效** |
| **啟動時間** | ~5秒 | ~0.5秒 | **10x** |
| **映像大小** | ~500MB | ~20MB | **25x** |

### 資源節省

#### 成本節省估算

假設使用雲端主機（如 AWS EC2）：

**Python 服務需求**:
- 實例類型: t3.medium（2 vCPU, 4GB RAM）
- 月費用: ~$30
- 記憶體使用: ~500MB
- CPU 使用: 60-80%

**Go 服務需求**:
- 實例類型: t3.small（2 vCPU, 2GB RAM）
- 月費用: ~$15
- 記憶體使用: ~100MB
- CPU 使用: 30-50%

**節省**:
- 成本節省: **50%** (~$15/月)
- 或相同成本下，可運行更多實例

### 維護性提升

| 方面 | Python | Go | 優勢 |
|-----|--------|-----|------|
| **部署複雜度** | 需要依賴安裝 | 單一執行檔 | ⭐⭐⭐⭐⭐ |
| **啟動速度** | 慢（需載入依賴） | 快（直接執行） | ⭐⭐⭐⭐⭐ |
| **錯誤檢測** | 執行時 | 編譯時 | ⭐⭐⭐⭐ |
| **類型安全** | 動態型別 | 靜態型別 | ⭐⭐⭐⭐⭐ |
| **併發複雜度** | 中（需小心 GIL） | 低（原生支援） | ⭐⭐⭐⭐⭐ |

### 可擴展性

#### 未來可遷移的模組

1. **投信外資爬蟲** - 估計提升 10-15 倍
2. **技術分析計算引擎**（使用 Rust）- 估計提升 20-100 倍
3. **即時行情推送**（WebSocket）- Go 原生支援，效能優異
4. **回測系統** - Go/Rust 高效能計算

#### 架構演進

```
Phase 1 (現在)
┌────────────┐
│   Python   │
│  Monolith  │
└────────────┘

Phase 2 (Go 爬蟲)
┌────────────┐    ┌────────┐
│   Python   │───▶│   Go   │
│   Backend  │    │Crawler │
└────────────┘    └────────┘

Phase 3 (微服務)
┌────────┐  ┌────────┐  ┌────────┐
│ Python │  │   Go   │  │  Rust  │
│  API   │  │Crawler │  │Analysis│
└────────┘  └────────┘  └────────┘

Phase 4 (完整微服務)
        ┌──────────────┐
        │ API Gateway  │
        └───────┬──────┘
        ┌───────┴────────┐
┌───────▼───┐  ┌─────▼──────┐
│    Go     │  │    Rust    │
│ Services  │  │  Services  │
└───────────┘  └────────────┘
```

### ROI（投資報酬率）分析

#### 投資成本

| 項目 | 成本 |
|-----|------|
| 開發時間 | 4-6 週 × 1 人 |
| 測試時間 | 包含在開發時程中 |
| 部署時間 | 2-3 天 |
| 學習成本 | Go 學習曲線適中 |
| **總成本** | **約 1-1.5 人月** |

#### 效益估算

| 效益 | 價值 |
|-----|------|
| 效能提升 | 每日節省 2-4 小時爬取時間 |
| 資源節省 | 雲端成本降低 50% |
| 可擴展性 | 支援未來功能擴展 |
| 技術能力 | 團隊掌握 Go 語言 |

**回本週期**: 估計 3-6 個月（根據雲端成本節省）

---

## 後續優化方向

### Phase 2: 進階功能（2-3 個月）

1. **遷移投信外資爬蟲**
   - 估計效能提升: 10-15 倍
   - 開發時間: 2-3 週

2. **實作即時資料推送（WebSocket）**
   - Go 原生支援高並發 WebSocket
   - 支援數萬並發連線
   - 開發時間: 3-4 週

3. **整合 gRPC 服務間通訊**
   - 提升服務間通訊效能
   - 強型別介面
   - 開發時間: 1-2 週

### Phase 3: 技術分析引擎（3-4 個月）

1. **使用 Rust 撰寫技術分析計算引擎**
   - 估計效能提升: 20-100 倍
   - 支援複雜技術指標計算
   - 開發時間: 6-8 週

2. **整合機器學習模型推理**
   - 使用 ONNX Runtime
   - 支援即時預測
   - 開發時間: 4-6 週

### Phase 4: 完整微服務架構（6-12 個月）

1. **服務拆分**
   - 爬蟲服務（Go） ✅
   - 計算服務（Rust）
   - 查詢服務（Go）
   - 使用者服務（Python/Go）
   - 分析服務（Python）

2. **基礎設施**
   - 服務網格（Istio/Linkerd）
   - API Gateway（Kong/APISIX）
   - 分散式追蹤（Jaeger）
   - 集中式日誌（ELK Stack）

---

## 附錄

### A. 參考資源

#### Go 學習資源
- [The Go Programming Language](https://go.dev/)
- [Effective Go](https://go.dev/doc/effective_go)
- [Go by Example](https://gobyexample.com/)

#### 技術文檔
- [Gin Web Framework](https://gin-gonic.com/)
- [sqlx Documentation](http://jmoiron.github.io/sqlx/)
- [Prometheus Go Client](https://prometheus.io/docs/guides/go-application/)

### B. 程式碼規範

#### Go 程式碼風格
- 遵循 [Effective Go](https://go.dev/doc/effective_go)
- 使用 `gofmt` 格式化程式碼
- 使用 `golangci-lint` 進行靜態檢查
- 遵循 [Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md)

#### 命名規範
- 套件名稱: 小寫單字，簡短有意義
- 介面名稱: 以 `er` 結尾（如 `Fetcher`, `Repository`）
- 常數: 大駝峰或全大寫
- 變數/函數: 駝峰式命名

### C. Git 工作流程

#### 分支策略
```
main
  ├── develop
  │   ├── feature/crawler-core
  │   ├── feature/database-integration
  │   ├── feature/api-endpoints
  │   └── feature/monitoring
  └── release/v1.0.0
```

#### Commit 訊息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: 修復錯誤
- `docs`: 文檔更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試
- `chore`: 建構流程或輔助工具

### D. 檢查清單

#### 開發完成檢查清單

- [ ] 所有單元測試通過
- [ ] 整合測試通過
- [ ] 程式碼覆蓋率 > 80%
- [ ] 通過 `golangci-lint` 檢查
- [ ] API 文檔更新
- [ ] README 更新

#### 上線前檢查清單

- [ ] 完整的端對端測試
- [ ] 效能基準測試完成
- [ ] 監控儀表板設置完成
- [ ] 告警規則配置完成
- [ ] 部署文檔撰寫完成
- [ ] 運維手冊撰寫完成
- [ ] 回滾計劃準備完成
- [ ] 團隊成員培訓完成

#### 上線後觀察清單

- [ ] 服務健康檢查正常
- [ ] 錯誤率在預期範圍內
- [ ] 回應延遲符合預期
- [ ] 資源使用正常
- [ ] 無記憶體洩漏
- [ ] 無 Goroutine 洩漏
- [ ] 資料一致性驗證通過

---

## 總結

本遷移計劃提供了一個**詳細、可執行的路線圖**，用於將 Python 爬蟲服務遷移至 Go 微服務。

### 關鍵成功因素

1. **漸進式實施** - 分階段實施，降低風險
2. **完全相容** - 確保 API 介面完全相容
3. **降級機制** - Go 失敗時自動降級到 Python
4. **充分測試** - 單元、整合、端對端測試覆蓋
5. **監控完善** - 完整的監控和告警體系

### 預期成果

- ✅ 效能提升 **10-20 倍**
- ✅ 資源使用降低 **60-80%**
- ✅ 部署簡化（單一執行檔）
- ✅ 為未來更多模組遷移奠定基礎
- ✅ 團隊掌握 Go 語言開發能力

### 下一步行動

1. 確認計劃並取得團隊共識
2. 準備開發環境
3. 按照第一週計劃開始實施
4. 定期檢視進度，及時調整計劃

---

**專案開始日期**: 2025-10-30
**預計完成日期**: 2025-12-15
**最後更新**: 2025-10-30
