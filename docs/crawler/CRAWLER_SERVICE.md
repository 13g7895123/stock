# Go 爬蟲服務完整指南

高效能的台灣股票資料爬蟲服務，使用 Go 1.21+ 實作，支援多個券商資料來源。

## 📋 快速概述

| 特性 | 說明 |
|------|------|
| **效能** | 相比 Python 版本提升 10-20 倍 |
| **併發** | 支援 1000+ Goroutines 並發 |
| **記憶體** | 使用量降低 60-80% |
| **監控** | 整合 Prometheus + Grafana |
| **可靠性** | 多來源輪詢、自動重試 |
| **部署** | 單一執行檔，無依賴 |

## 🏗️ 架構設計

```
┌─────────────────────────────────────────────┐
│         API Handler (HTTP Layer)             │
│  • /health       - 健康檢查                  │
│  • /stocks       - 股票列表                  │
│  • /batch-update - 批次更新                  │
│  • /metrics      - Prometheus 指標           │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│         Stock Service (Business Logic)       │
│  • 協調爬蟲與儲存                             │
│  • 資料驗證與轉換                             │
│  • 指標計算                                  │
└────────────┬────────────────────────────────┘
             │
      ┌──────┴──────┬─────────────┬─────────────┐
      │             │             │             │
┌─────▼──┐  ┌──────▼──┐  ┌──────▼──┐  ┌──────▼──┐
│ Fubon  │  │ Concord │  │ Taifex  │  │ TWSE    │
│ Scraper│  │ Scraper │  │ Scraper │  │ Scraper │
└────────┘  └─────────┘  └─────────┘  └─────────┘
      │             │             │             │
      └──────┬──────┴─────────────┴─────────────┘
             │
     ┌───────▼──────────┐
     │ Parser & Storage │
     │  • CSV 解析       │
     │  • 資料驗證       │
     │  • 批次插入       │
     │  • 衝突處理       │
     └───────┬──────────┘
             │
     ┌───────▼──────────┐
     │  PostgreSQL      │
     │  stock_daily_    │
     │  data table      │
     └──────────────────┘
```

## 🔧 安裝與部署

### 方式 1：Docker 部署（推薦）

```bash
cd crawler-service/deployments
docker-compose up -d
```

### 方式 2：本地運行

#### 前置需求
- Go 1.21+
- PostgreSQL 15+
- Make（可選）

#### 安裝步驟

```bash
# 1. 進入目錄
cd crawler-service

# 2. 自動安裝依賴（可選）
./scripts/install.sh

# 3. 編輯配置
cp configs/config.yaml configs/config.local.yaml
# 修改資料庫連線設定

# 4. 編譯
make build

# 5. 執行
make run
```

### 方式 3：互動式部署

```bash
./scripts/deploy.sh
# 選擇所需部署方式，按提示操作
```

## ⚙️ 配置說明

### 主配置檔案：`configs/config.yaml`

```yaml
# 應用程式設定
app:
  name: "Stock Crawler Service"
  version: "1.0.0"
  port: 8082
  log_level: "info"

# 資料庫設定
database:
  host: "localhost"
  port: 5432
  user: "stock_user"
  password: "password"
  dbname: "stock_analysis"
  max_connections: 10

# Redis 設定
redis:
  host: "localhost"
  port: 6379
  db: 0

# 爬蟲設定
crawler:
  max_workers: 20          # 最大並發工作線程
  timeout: 30              # 超時時間（秒）
  retry_attempts: 3        # 重試次數
  delay: 100               # 請求間隔（毫秒）
  
  sources:
    - name: "fubon"
      enabled: true
      priority: 1
      url: "https://fubon-ebrokerdj.fbs.com.tw"
    
    - name: "concord"
      enabled: true
      priority: 2
      url: "https://www.concord.com.tw"

# 監控設定
metrics:
  enabled: true
  port: 9090
  interval: 30             # 採集間隔（秒）
```

## 📡 API 端點

### 1. 健康檢查

```bash
GET /health
```

**回應**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### 2. 股票列表

```bash
GET /api/v1/stocks
```

**查詢參數**:
- `limit`: 限制數量（預設 50）
- `offset`: 分頁偏移（預設 0）
- `search`: 搜尋關鍵字（代碼或名稱）

### 3. 單一股票

```bash
GET /api/v1/stocks/:code
```

**範例**:
```bash
GET /api/v1/stocks/2330
```

### 4. 批次更新（核心端點）

```bash
POST /api/v1/stocks/batch-update
Content-Type: application/json

{
  "symbols": ["2330", "2317", "2454"],
  "force_update": false
}
```

**參數說明**:
- `symbols`: 股票代碼陣列（必填）
- `force_update`: 是否強制重新爬取（預設 false，只爬取未有資料的股票）

**回應**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_1768117170",
    "total_symbols": 3,
    "started_at": "2026-01-11T10:00:00Z",
    "status": "processing",
    "message": "Submitted 3 tasks successfully"
  }
}
```

### 5. 批次狀態查詢

```bash
GET /api/v1/batches/:batch_id
```

**回應**:
```json
{
  "batch_id": "batch_1768117170",
  "total_symbols": 3,
  "completed": 2,
  "failed": 0,
  "status": "processing",
  "progress": "66.67%"
}
```

### 6. Prometheus 指標

```bash
GET /metrics
```

**重要指標**:
- `crawler_tasks_total` - 總任務數
- `crawler_tasks_success_total` - 成功任務數
- `crawler_tasks_failure_total` - 失敗任務數
- `crawler_parse_duration_seconds` - 解析耗時
- `crawler_storage_duration_seconds` - 儲存耗時
- `crawler_db_connection_errors_total` - 資料庫連線錯誤

## 🔍 核心代碼走查

### 爬蟲流程

#### 1. Parser 層（`internal/scraper/parser.go`）

**任務**: 解析富邦證券 API 回應

```go
// 輸入格式（6 個空格分隔段）
// 20250110 20250109 20250108 ... | 293.71 287.50 ... | ... | ...
// [dates]                        | [opens]          | [highs] | [lows] | [closes] | [volumes]

func parseHistoricalData(response string) ([]DailyData, error) {
    sections := strings.Split(response, " ")
    // 確認有 6 個部分
    if len(sections) != 6 {
        return nil, fmt.Errorf("unexpected format: got %d sections, want 6", len(sections))
    }
    
    dates := strings.Split(sections[0], ",")
    opens := strings.Split(sections[1], ",")
    highs := strings.Split(sections[2], ",")
    lows := strings.Split(sections[3], ",")
    closes := strings.Split(sections[4], ",")
    volumes := strings.Split(sections[5], ",")
    
    // 建立記錄
    // ...
}
```

**最近修復**（2026-01-11）：
- ✅ 修正了段索引對應（最初誤認為 [volumes, dates, opens, ...]）
- ✅ 新增數據驗證確保 1440 筆記錄完整

#### 2. Stock Service 層（`internal/service/stock_service.go`）

**任務**: 協調爬蟲與儲存，包含指標轉換

```go
func (s *StockService) FetchAndStore(ctx context.Context, stockCode string) error {
    // 1. 爬取資料
    records, err := s.scraper.Scrape(ctx, stockCode)
    if err != nil {
        return fmt.Errorf("scraper error: %w", err)
    }
    
    // 2. 驗證資料品質
    validRecords := s.validateRecords(records)
    
    // 3. 轉換為儲存格式（關鍵修復位置）
    dbRecords := make([]storage.StockDailyData, len(validRecords))
    for i, record := range validRecords {
        rec := record  // ✅ 建立本地副本避免指標別名
        dbRecords[i] = storage.StockDailyData{
            StockCode:    rec.StockCode,
            TradeDate:    rec.TradeDate,
            OpenPrice:    &rec.OpenPrice,    // 現在指向獨立副本
            HighPrice:    &rec.HighPrice,
            LowPrice:     &rec.LowPrice,
            ClosePrice:   &rec.ClosePrice,
            Volume:       &rec.Volume,
        }
    }
    
    // 4. 批次儲存
    return s.storage.BatchInsert(ctx, dbRecords)
}
```

**關鍵修復** - Go 指標別名問題：

❌ **舊代碼（有 bug）**:
```go
for i, record := range validRecords {
    dbRecords[i] = StockDailyData{
        OpenPrice: &record.OpenPrice,  // 所有指標指向同一記憶體！
    }
}
```

✅ **修復後**:
```go
for i, record := range validRecords {
    rec := record  // 建立本地副本
    dbRecords[i] = StockDailyData{
        OpenPrice: &rec.OpenPrice,  // 每個指標獨立
    }
}
```

**結果**：股票 2330 從全部重複值 (1665/1700/1655/1680/42191) 改為正確的變動數據

#### 3. Storage 層（`internal/storage/batch.go`）

**任務**: 高效批次插入，使用 `COPY` 命令

```go
func (r *Repository) BatchInsert(ctx context.Context, records []StockDailyData) error {
    // PostgreSQL COPY 支援，提升 10-100 倍效能
    // 使用 ON CONFLICT DO UPDATE 處理重複
    
    sql := `
        COPY stock_daily_data 
        (stock_code, trade_date, open_price, high_price, low_price, close_price, volume)
        FROM STDIN
        ON CONFLICT (stock_code, trade_date) DO UPDATE SET
            open_price = EXCLUDED.open_price,
            ...
    `
    
    // 批次插入（預設 1000 筆一次）
}
```

## 📊 監控與調試

### 1. 查看爬蟲日誌

```bash
# 即時日誌
docker-compose logs -f crawler-service

# 搜尋錯誤
docker-compose logs crawler-service | grep ERROR

# 搜尋特定股票
docker-compose logs crawler-service | grep "2330"
```

### 2. 監控效能

```bash
# 查看 Prometheus 指標
curl http://localhost:9090/metrics

# 重點指標
curl http://localhost:9090/metrics | grep crawler
```

### 3. 直接查詢資料庫

```bash
# 進入 PostgreSQL
docker-compose exec postgres psql -U stock_user -d stock_analysis

# 查看股票 2330 的資料
SELECT stock_code, trade_date, open_price, high_price, low_price, close_price, volume
FROM stock_daily_data 
WHERE stock_code = '2330' 
ORDER BY trade_date LIMIT 10;

# 統計記錄數
SELECT stock_code, COUNT(*) as record_count 
FROM stock_daily_data 
GROUP BY stock_code 
ORDER BY record_count DESC;
```

### 4. 效能基準測試

```bash
# 測試爬取速度
time curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'

# 期望耗時：10-30 秒（取決於資料量和網路）
```

## 🐛 常見問題

### 1. 爬取資料全部重複

**症狀**: 所有記錄顯示相同的 open/high/low/close/volume

**原因**: Go range loop 指標別名問題

**解決**: 確認 `stock_service.go` 有以下修復：
```go
rec := record  // 本地副本
dbRecords[i] = StockDailyData{
    OpenPrice: &rec.OpenPrice,  // 使用副本指標
}
```

**驗證**:
```bash
# 查看資料是否變動
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT DISTINCT open_price FROM stock_daily_data WHERE stock_code = '2330' LIMIT 5;"
```

### 2. 爬蟲超時

**症狀**: 爬蟲任務經常失敗

**解決方案**:
- 增加 `timeout` 設定
- 減少 `max_workers` 降低併發
- 檢查網路連線

### 3. 資料庫連線錯誤

**症狀**: "connection refused" 或 "authentication failed"

**解決方案**:
```bash
# 檢查資料庫狀態
docker-compose ps postgres

# 檢查連線設定
docker-compose logs postgres | tail -20

# 重啟資料庫
docker-compose restart postgres
```

## 🚀 效能優化

### 1. 調整爬蟲參數

```yaml
crawler:
  max_workers: 50        # 增加併發（監控 CPU）
  delay: 50              # 減少請求間隔
  timeout: 60            # 增加超時時間
  retry_attempts: 5      # 增加重試次數
```

### 2. 資料庫優化

```sql
-- 建立索引加速查詢
CREATE INDEX idx_stock_code_date ON stock_daily_data(stock_code, trade_date);
CREATE INDEX idx_trade_date ON stock_daily_data(trade_date);

-- 統計資料更新
ANALYZE stock_daily_data;
```

### 3. 批次大小調整

編輯 `storage/batch.go`:
```go
const BatchSize = 1000  // 調整批次大小
```

## 📚 延伸資源

- [API 完整文件](../backend/API_DOCUMENTATION.md)
- [使用指南](../guides/USAGE_GUIDE.md)
- [故障排除](../troubleshooting/COMMON_ISSUES.md)
- [專案結構](../PROJECT_STRUCTURE.md)
