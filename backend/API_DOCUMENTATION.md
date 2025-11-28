# 股票分析系統 API 文件

> **版本**: 1.0.0  
> **基礎 URL**: `http://localhost:9127/api/v1`  
> **Swagger UI**: `http://localhost:9127/docs`  
> **ReDoc**: `http://localhost:9127/redoc`

---

## 目錄

1. [概述](#概述)
2. [認證](#認證)
3. [通用回應格式](#通用回應格式)
4. [錯誤處理](#錯誤處理)
5. [API 端點](#api-端點)
   - [健康檢查 (Health Check)](#健康檢查-health-check)
   - [股票管理 (Stocks)](#股票管理-stocks)
   - [股票同步 (Stock Synchronization)](#股票同步-stock-synchronization)
   - [每日資料 (Data Management)](#每日資料-data-management)
   - [歷史資料 (Stock History)](#歷史資料-stock-history)
   - [均線計算 (Moving Averages)](#均線計算-moving-averages)
   - [選股功能 (Stock Selection)](#選股功能-stock-selection)
   - [投信外資買賣超 (Institutional Trading)](#投信外資買賣超-institutional-trading)
   - [股本資料 (Capital Stock)](#股本資料-capital-stock)
   - [交易日分析 (Trading Days)](#交易日分析-trading-days)
   - [任務管理 (Task Management)](#任務管理-task-management)
   - [任務執行紀錄 (Task Execution)](#任務執行紀錄-task-execution)
   - [證交所 API (TWSE)](#證交所-api-twse)
6. [使用範例](#使用範例)

---

## 概述

本系統提供台灣股市資料分析的完整 REST API，包含：

- 📊 **股票資料管理** - 股票清單、每日交易資料、歷史資料
- 📈 **技術分析** - 均線計算、選股策略
- 🏦 **法人資料** - 投信、外資、自營商買賣超
- ⏱️ **任務管理** - 非同步爬蟲任務、資料更新
- 📡 **外部 API** - 證交所即時資料接口

---

## 認證

目前系統為開發模式，**無需認證**即可使用所有 API。

---

## 通用回應格式

### 成功回應

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-11-28T12:00:00.000000"
}
```

### 分頁回應

```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1908,
    "total_pages": 39,
    "has_next": true,
    "has_previous": false
  },
  "timestamp": "2025-11-28T12:00:00.000000"
}
```

---

## 錯誤處理

### HTTP 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| `200` | 請求成功 |
| `201` | 資源已建立 |
| `400` | 請求參數錯誤 |
| `404` | 資源不存在 |
| `422` | 驗證錯誤 |
| `500` | 伺服器內部錯誤 |

### 錯誤回應格式

```json
{
  "detail": "錯誤訊息描述"
}
```

### 驗證錯誤格式

```json
{
  "detail": [
    {
      "loc": ["query", "parameter_name"],
      "msg": "錯誤訊息",
      "type": "value_error"
    }
  ]
}
```

---

## API 端點

---

### 健康檢查 (Health Check)

用於監控系統運行狀態。

#### GET `/health/`
基本健康檢查

**回應範例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-28T13:21:48.465217",
  "version": "1.0.0",
  "environment": "development"
}
```

#### GET `/health/detailed`
詳細健康檢查（包含資料庫、Redis 狀態）

**回應範例**:
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  },
  "timestamp": "2025-11-28T13:21:48.465217"
}
```

#### GET `/health/liveness`
存活探針 (Kubernetes 用)

#### GET `/health/readiness`
就緒探針 (Kubernetes 用)

---

### 股票管理 (Stocks)

核心股票資料操作。

#### GET `/stocks/list`
取得股票清單

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `page` | integer | 1 | 頁數 (≥1) |
| `limit` | integer | 50 | 每頁筆數 (1-1000) |
| `market` | string | - | 市場篩選 (`TSE`/`TPEx`) |
| `search` | string | - | 搜尋股票代號或名稱 |

**請求範例**:
```bash
curl "http://localhost:9127/api/v1/stocks/list?page=1&limit=10&market=TSE&search=台積"
```

**回應範例**:
```json
{
  "status": "success",
  "stocks": [
    {
      "code": "2330",
      "name": "台積電",
      "market": "TSE",
      "industry": "半導體業",
      "price": 0.0,
      "change": 0.0,
      "dataStatus": "complete",
      "lastUpdate": "即時"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1908,
    "total_pages": 191,
    "has_next": true,
    "has_previous": false
  },
  "timestamp": "2025-11-28T13:21:48.465217"
}
```

#### GET `/stocks/symbols`
取得可用股票代碼列表

#### GET `/stocks/{symbol}/current`
取得股票當前價格

**路徑參數**:
- `symbol` (string, required): 股票代碼，如 `2330`

#### GET `/stocks/{symbol}/historical`
取得股票歷史資料

**路徑參數**:
- `symbol` (string, required): 股票代碼

**查詢參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `start_date` | date | ✓ | 開始日期 (YYYY-MM-DD) |
| `end_date` | date | ✓ | 結束日期 (YYYY-MM-DD) |

**請求範例**:
```bash
curl "http://localhost:9127/api/v1/stocks/2330/historical?start_date=2025-01-01&end_date=2025-11-28"
```

#### POST `/stocks/{symbol}/update`
觸發單一股票資料更新

**請求範例**:
```bash
curl -X POST "http://localhost:9127/api/v1/stocks/2330/update"
```

**回應範例**:
```json
{
  "message": "Data update triggered for 2330",
  "task_id": "abc123-def456",
  "status": "queued",
  "timestamp": "2025-11-28T13:21:48.465217"
}
```

#### POST `/stocks/update-all`
批次更新所有或指定股票

**請求 Body**:
```json
{
  "symbols": ["2330", "2317", "2454"]
}
```
> 若不提供 `symbols`，將更新資料庫中所有啟用的股票

#### GET `/stocks/{symbol}/analysis`
取得股票技術分析結果

**查詢參數**:
- `indicators` (array): 技術指標列表，可選 `SMA`, `EMA`, `RSI`, `MACD`, `BB`, `STOCH`

#### POST `/stocks/{symbol}/analyze`
觸發股票技術分析

#### GET `/stocks/{symbol}/signals`
取得股票交易訊號

#### POST `/stocks/signals/generate`
批次產生交易訊號

---

### 股票同步 (Stock Synchronization)

與外部資料源同步股票清單。

#### GET `/sync/stocks/crawl`
從證交所爬取最新股票清單

**回應範例**:
```json
{
  "status": "success",
  "fetched_count": 1908,
  "stocks": [...]
}
```

#### POST `/sync/stocks/sync`
將爬取的股票清單同步至資料庫

**回應範例**:
```json
{
  "status": "success",
  "created": 50,
  "updated": 1858,
  "total": 1908
}
```

#### GET `/sync/stocks/count`
取得股票數量統計

#### GET `/sync/stocks/validate/{symbol}`
驗證股票代碼是否存在

---

### 每日資料 (Data Management)

每日交易資料管理。

#### GET `/data/daily/{symbol}`
取得股票每日交易資料

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `start_date` | date | - | 開始日期 |
| `end_date` | date | - | 結束日期 |
| `limit` | integer | 100 | 限制筆數 |

#### GET `/data/daily/{symbol}/latest`
取得股票最新資料日期

#### POST `/data/daily/batch-update`
批次更新每日資料

**請求 Body**:
```json
{
  "symbols": ["2330", "2317"],
  "start_date": "2025-01-01",
  "end_date": "2025-11-28"
}
```

#### POST `/data/daily/concurrent-batch-update`
並行批次更新每日資料（高效能）

**請求 Body**:
```json
{
  "symbols": ["2330", "2317", "2454"],
  "max_workers": 4,
  "timeout_per_stock": 120.0,
  "batch_size": 10
}
```

---

### 歷史資料 (Stock History)

股票歷史資料查詢與統計。

#### GET `/data/history/{symbol}`
取得股票完整歷史資料

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `limit` | integer | 100 | 限制筆數 |
| `offset` | integer | 0 | 偏移量 |

#### GET `/data/history/{symbol}/stats`
取得股票資料統計

**回應範例**:
```json
{
  "symbol": "2330",
  "total_records": 5000,
  "date_range": {
    "start": "2005-01-03",
    "end": "2025-11-27"
  },
  "missing_dates": 5
}
```

#### GET `/data/history/{symbol}/latest-date`
取得股票最新交易日期

#### GET `/data/history/overview`
取得整體資料統計概況

#### GET `/data/history/stocks-with-data`
取得有資料的股票列表

---

### 均線計算 (Moving Averages)

技術分析均線計算服務。

#### POST `/moving-averages/calculate`
計算均線（同步）

**請求 Body**:
```json
{
  "stock_codes": ["2330", "2317", "2454"],
  "periods": [5, 10, 24, 72, 120, 240],
  "force_recalculate": false
}
```

**回應範例**:
```json
{
  "status": "success",
  "processed_count": 3,
  "results": {
    "2330": { "success": true, "records_updated": 5000 },
    "2317": { "success": true, "records_updated": 4800 },
    "2454": { "success": true, "records_updated": 4500 }
  }
}
```

#### POST `/moving-averages/calculate-async`
計算均線（非同步）

**請求 Body**:
```json
{
  "stock_codes": null,
  "periods": [5, 10, 24, 72, 120, 240],
  "force_recalculate": false,
  "batch_size": 50
}
```
> `stock_codes` 為 `null` 時計算所有有資料的股票

**回應範例**:
```json
{
  "task_id": "abc123-def456",
  "status": "queued",
  "message": "均線計算任務已排入佇列"
}
```

#### GET `/moving-averages/task-status/{task_id}`
查詢非同步任務狀態

#### DELETE `/moving-averages/task/{task_id}`
取消非同步任務

#### GET `/moving-averages/query/{stock_code}`
查詢股票均線資料

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `periods` | array | [5,10,24,72,120,240] | 均線週期 |
| `limit` | integer | 100 | 限制筆數 |

**回應範例**:
```json
{
  "stock_code": "2330",
  "data": [
    {
      "date": "2025-11-27",
      "close": 1050.0,
      "ma5": 1048.2,
      "ma10": 1045.5,
      "ma24": 1030.8,
      "ma72": 1010.2,
      "ma120": 995.6,
      "ma240": 920.3
    }
  ],
  "count": 100
}
```

#### GET `/moving-averages/statistics`
獲取均線計算統計資訊

#### GET `/moving-averages/validate`
驗證均線資料一致性

#### POST `/moving-averages/clear`
清除均線資料

---

### 選股功能 (Stock Selection)

根據均線策略進行選股。

#### GET `/stock-selection/results`
取得選股結果

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `strategy` | string | `all_ma_above` | 選股策略 |
| `limit` | integer | 50 | 限制筆數 |

**可用策略**:
- `all_ma_above`: 股價在所有均線之上
- `ma_golden_cross`: 均線黃金交叉
- `ma_death_cross`: 均線死亡交叉
- `volume_breakout`: 成交量突破

#### GET `/stock-selection/latest-date`
取得最新交易日期

#### GET `/stock-selection/stock/{stock_code}/ma-status`
取得個股均線狀態

**回應範例**:
```json
{
  "stock_code": "2330",
  "date": "2025-11-27",
  "close": 1050.0,
  "ma_status": {
    "above_ma5": true,
    "above_ma10": true,
    "above_ma24": true,
    "above_ma72": true,
    "above_ma120": true,
    "above_ma240": true
  },
  "all_above": true
}
```

---

### 投信外資買賣超 (Institutional Trading)

法人買賣超資料。

#### POST `/institutional-trading/update/{date}`
更新指定日期的投信外資買賣超資料

**路徑參數**:
- `date` (string, required): 交易日期，格式 `YYYYMMDD`

**請求範例**:
```bash
curl -X POST "http://localhost:9127/api/v1/institutional-trading/update/20251127"
```

**回應範例**:
```json
{
  "status": "success",
  "date": "20251127",
  "total_processed": 1908,
  "created_count": 100,
  "updated_count": 1808,
  "error_count": 0
}
```

#### POST `/institutional-trading/update/batch`
批次更新近期投信外資買賣超資料

**查詢參數**:
- `days_back` (integer, 1-365, default: 30): 回溯天數

#### POST `/institutional-trading/update/latest`
更新最新交易日的資料

#### GET `/institutional-trading/stock/{stock_code}`
取得特定股票的投信外資買賣超資料

**查詢參數**:
- `limit` (integer, 1-365, default: 30): 限制筆數

**回應範例**:
```json
{
  "stock_code": "2330",
  "data": [
    {
      "date": "2025-11-27",
      "foreign_buy": 15000,
      "foreign_sell": 12000,
      "foreign_net": 3000,
      "investment_trust_buy": 500,
      "investment_trust_sell": 200,
      "investment_trust_net": 300,
      "dealer_buy": 1000,
      "dealer_sell": 800,
      "dealer_net": 200,
      "total_net": 3500
    }
  ],
  "total_records": 30
}
```

#### GET `/institutional-trading/summary/{date}`
取得指定日期的投信外資買賣超總覽

#### GET `/institutional-trading/rankings/latest`
取得最新交易日的買賣超排名

**查詢參數**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `category` | string | `total` | 排名類別：`foreign`, `investment_trust`, `dealer`, `total` |
| `limit` | integer | 20 | 筆數 (1-100) |
| `sort_by` | string | `amount` | 排序方式：`amount`, `capital_ratio` |

#### GET `/institutional-trading/rankings/{date}`
取得指定日期的買賣超排名

#### GET `/institutional-trading/capital-ratio/rankings`
取得股本比累積排名

**查詢參數**:
- `days_back` (integer, 1-365, default: 30): 回溯天數
- `limit` (integer, 1-100, default: 50): 筆數

#### GET `/institutional-trading/capital-ratio/trends`
取得每日股本比趨勢資料

#### GET `/institutional-trading/check/completeness`
檢查投信外資買賣超資料的完整性

#### GET `/institutional-trading/statistics`
取得投信外資買賣超統計

---

### 股本資料 (Capital Stock)

股票股本資料管理。

#### GET `/capital-stock/{stock_code}`
取得股票股本資料

**回應範例**:
```json
{
  "stock_code": "2330",
  "capital": 259303804580,
  "shares_outstanding": 25930380458,
  "last_updated": "2025-11-27"
}
```

#### POST `/capital-stock/update`
更新所有股票股本資料

#### GET `/capital-stock/statistics`
取得股本資料統計

#### GET `/capital-stock/check/completeness`
檢查股本資料完整性

---

### 交易日分析 (Trading Days Analysis)

分析交易日資料缺漏。

#### GET `/trading-days/info`
取得交易日服務資訊

#### GET `/trading-days/missing-summary`
取得缺漏交易日摘要

#### GET `/trading-days/smart-analysis`
智慧分析缺漏交易日

**回應範例**:
```json
{
  "analysis_date": "2025-11-28",
  "stocks_analyzed": 1908,
  "stocks_with_missing_data": 150,
  "total_missing_days": 450,
  "recommendations": [
    {
      "priority": "high",
      "action": "更新 2330 的 2025-11-25 至 2025-11-27 資料"
    }
  ]
}
```

#### GET `/trading-days/smart-batch-update-analysis`
智慧批次更新分析

#### GET `/trading-days/stock-completeness`
取得股票資料完整性摘要

#### POST `/trading-days/fix-suggestions`
取得缺漏資料修復建議

---

### 任務管理 (Task Management)

爬蟲與資料處理任務管理。

#### GET `/tasks/manual`
取得手動任務列表

#### GET `/tasks/manual/{task_id}`
取得任務詳情

**回應範例**:
```json
{
  "task_id": "abc123-def456",
  "task_type": "stock_crawl",
  "status": "running",
  "progress": 45.5,
  "created_at": "2025-11-28T10:00:00",
  "started_at": "2025-11-28T10:00:05",
  "completed_at": null,
  "result": null,
  "error": null
}
```

#### DELETE `/tasks/manual/{task_id}`
取消任務

#### POST `/tasks/manual/stock-crawl`
建立股票爬蟲任務

**請求 Body**:
```json
{
  "symbols": ["2330", "2317", "2454"]
}
```

#### POST `/tasks/manual/optimized-stock-crawl`
建立優化股票爬蟲任務（高效能）

**請求 Body**:
```json
{
  "symbols": null,
  "max_workers": 4,
  "batch_size": 50,
  "enable_smart_skip": true,
  "enable_batch_db_operations": true,
  "smart_skip_days": 1
}
```

**參數說明**:
| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `symbols` | array | null | 股票代碼清單，為空則更新所有股票 |
| `max_workers` | integer | 4 | 並行處理線程數量 (1-16) |
| `batch_size` | integer | 50 | 批次處理大小 (1-500) |
| `enable_smart_skip` | boolean | true | 啟用智能跳過機制 |
| `enable_batch_db_operations` | boolean | true | 啟用批次資料庫操作 |
| `smart_skip_days` | integer | 1 | 智能跳過天數 (0-30) |

#### POST `/tasks/manual/sequential-stock-crawl`
建立循序股票爬蟲任務（低資源消耗）

**請求 Body**:
```json
{
  "symbols": null,
  "batch_size": 477,
  "delay_between_stocks": 0.5,
  "delay_between_batches": 10.0,
  "cpu_threshold": 80.0,
  "memory_threshold": 85.0,
  "auto_pause_on_overload": true
}
```

#### POST `/tasks/manual/clear-completed`
清除已完成的任務

---

### 任務執行紀錄 (Task Execution Logs)

任務執行歷史與監控。

#### GET `/task-execution/recent`
取得最近任務執行紀錄

**查詢參數**:
- `limit` (integer, default: 20): 筆數

#### GET `/task-execution/running`
取得正在執行的任務

#### GET `/task-execution/status/{task_id}`
取得任務執行狀態

#### GET `/task-execution/statistics`
取得任務執行統計

#### POST `/task-execution/cancel/{task_id}`
取消正在執行的任務

---

### 證交所 API (TWSE Official API)

直接存取證交所公開資料。

#### GET `/twse/info`
取得 TWSE API 資訊

#### GET `/twse/stock/{symbol}`
取得單一股票即時資料

**請求範例**:
```bash
curl "http://localhost:9127/api/v1/twse/stock/2330"
```

#### GET `/twse/daily-all`
取得當日所有股票資料

#### GET `/twse/historical/{symbol}`
取得股票歷史資料

**查詢參數**:
- `date` (string): 日期，格式 `YYYYMMDD`

#### GET `/twse/historical-all/{date}`
取得指定日期所有股票資料

#### GET `/twse/market-summary`
取得市場摘要

---

## 使用範例

### 完整工作流程範例

#### 1. 同步股票清單

```bash
# 從證交所爬取股票清單
curl -X GET "http://localhost:9127/api/v1/sync/stocks/crawl"

# 同步到資料庫
curl -X POST "http://localhost:9127/api/v1/sync/stocks/sync"
```

#### 2. 更新股票資料

```bash
# 使用優化爬蟲更新所有股票
curl -X POST "http://localhost:9127/api/v1/tasks/manual/optimized-stock-crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": null,
    "max_workers": 4,
    "batch_size": 50
  }'

# 查詢任務狀態
curl "http://localhost:9127/api/v1/tasks/manual/{task_id}"
```

#### 3. 計算均線

```bash
# 非同步計算所有股票均線
curl -X POST "http://localhost:9127/api/v1/moving-averages/calculate-async" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": null,
    "periods": [5, 10, 24, 72, 120, 240],
    "force_recalculate": false,
    "batch_size": 50
  }'
```

#### 4. 選股

```bash
# 取得股價在所有均線之上的股票
curl "http://localhost:9127/api/v1/stock-selection/results?strategy=all_ma_above&limit=20"
```

#### 5. 查詢法人買賣超

```bash
# 更新最新法人資料
curl -X POST "http://localhost:9127/api/v1/institutional-trading/update/latest"

# 取得買超排名
curl "http://localhost:9127/api/v1/institutional-trading/rankings/latest?category=foreign&limit=10"
```

### Python 範例

```python
import requests

BASE_URL = "http://localhost:9127/api/v1"

# 取得股票清單
def get_stock_list(page=1, limit=50, market=None):
    params = {"page": page, "limit": limit}
    if market:
        params["market"] = market
    
    response = requests.get(f"{BASE_URL}/stocks/list", params=params)
    return response.json()

# 取得股票均線資料
def get_moving_averages(stock_code, periods=None, limit=100):
    params = {"limit": limit}
    if periods:
        params["periods"] = periods
    
    response = requests.get(
        f"{BASE_URL}/moving-averages/query/{stock_code}",
        params=params
    )
    return response.json()

# 觸發資料更新
def trigger_update(symbols=None):
    data = {"symbols": symbols} if symbols else {}
    
    response = requests.post(
        f"{BASE_URL}/tasks/manual/optimized-stock-crawl",
        json=data
    )
    return response.json()

# 使用範例
if __name__ == "__main__":
    # 取得前 10 檔上市股票
    stocks = get_stock_list(page=1, limit=10, market="TSE")
    print(f"取得 {len(stocks['stocks'])} 檔股票")
    
    # 取得台積電均線資料
    ma_data = get_moving_averages("2330", limit=10)
    print(f"取得 {len(ma_data.get('data', []))} 筆均線資料")
```

### JavaScript 範例

```javascript
const BASE_URL = "http://localhost:9127/api/v1";

// 取得股票清單
async function getStockList(page = 1, limit = 50, market = null) {
  const params = new URLSearchParams({ page, limit });
  if (market) params.append("market", market);
  
  const response = await fetch(`${BASE_URL}/stocks/list?${params}`);
  return response.json();
}

// 取得股票均線資料
async function getMovingAverages(stockCode, limit = 100) {
  const response = await fetch(
    `${BASE_URL}/moving-averages/query/${stockCode}?limit=${limit}`
  );
  return response.json();
}

// 觸發資料更新
async function triggerUpdate(symbols = null) {
  const response = await fetch(
    `${BASE_URL}/tasks/manual/optimized-stock-crawl`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols }),
    }
  );
  return response.json();
}

// 使用範例
(async () => {
  const stocks = await getStockList(1, 10, "TSE");
  console.log(`取得 ${stocks.stocks.length} 檔股票`);
  
  const maData = await getMovingAverages("2330", 10);
  console.log(`取得 ${maData.data?.length || 0} 筆均線資料`);
})();
```

---

## 附錄

### 股票代碼格式

- **上市 (TSE)**: 4 位數字，如 `2330`
- **上櫃 (TPEx)**: 4 位數字，如 `6547`

### 日期格式

| 格式 | 說明 | 範例 |
|------|------|------|
| `YYYY-MM-DD` | ISO 格式 | `2025-11-28` |
| `YYYYMMDD` | 證交所格式 | `20251128` |

### 均線週期

| 週期 | 名稱 | 說明 |
|------|------|------|
| 5 | 週線 | 5 日移動平均 |
| 10 | 雙週線 | 10 日移動平均 |
| 24 | 月線 | 24 日移動平均 |
| 72 | 季線 | 72 日移動平均 |
| 120 | 半年線 | 120 日移動平均 |
| 240 | 年線 | 240 日移動平均 |

### 法人類別

| 代碼 | 名稱 |
|------|------|
| `foreign` | 外資 |
| `investment_trust` | 投信 |
| `dealer` | 自營商 |
| `total` | 三大法人合計 |

---

> **文件最後更新**: 2025-11-28  
> **API 版本**: 1.0.0
