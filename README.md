# Stock Crawler Service

> 高效能台灣股票資料爬蟲服務 | High-Performance Taiwan Stock Data Crawler

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://golang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-Private-red?style=flat)](LICENSE)

---

## 📖 簡介

本專案提供高效能的台灣股票歷史資料爬蟲服務，使用 Go 語言開發，支援從多個券商網站爬取股票日線資料並儲存至 PostgreSQL 資料庫。

### ✨ 特色

- ⚡ **高效能**: 相比 Python 版本提升 10-20 倍效能
- 🚀 **高併發**: 支援 1000+ Goroutines 並發處理
- 💾 **低資源**: 記憶體使用降低 60-80%
- 📦 **易部署**: 單一執行檔，Docker 一鍵啟動
- 🔄 **容錯性**: 多資料源輪詢，自動重試機制
- 📊 **可監控**: 整合 Prometheus metrics

### 🎯 核心功能

- **股票資料爬取**: 支援從富邦、群益等券商網站爬取歷史日線資料
- **批次處理**: 批次更新多支股票，自動管理併發任務
- **資料驗證**: 自動驗證資料完整性與正確性
- **RESTful API**: 提供完整的 HTTP API 介面
- **健康檢查**: 內建健康檢查與服務狀態監控

---

## 🚀 快速開始

### 前置需求

- **Docker** 20.10+ 與 **Docker Compose** 1.29+
- （可選）Go 1.21+ 用於本地開發

### 一鍵啟動

```bash
# 克隆專案
git clone https://github.com/13g7895123/stock.git
cd stock

# 複製環境變數範例
cp .env.example .env

# 啟動服務
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

### 驗證安裝

```bash
# 檢查爬蟲服務健康狀態
curl http://localhost:9627/health

# 預期回應:
# {"status":"ok","database":"connected","timestamp":"2026-01-11T10:00:00Z"}
```

---

## 📡 API 使用

### 1. 健康檢查

```bash
GET http://localhost:9627/health
```

### 2. 批次更新股票資料

```bash
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454"]}'
```

**回應範例:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_1768117170",
    "total_symbols": 3,
    "started_at": "2026-01-11T10:00:00Z",
    "status": "processing"
  }
}
```

### 3. 查詢股票資料

```bash
# 查詢單一股票
curl http://localhost:9627/api/v1/stocks/2330

# 查詢股票列表
curl http://localhost:9627/api/v1/stocks
```

### 4. Prometheus 指標

```bash
curl http://localhost:9627/metrics
```

---

## 🏗️ 專案結構

```
stock/
├── crawler-service/        # Go 爬蟲服務主目錄
│   ├── cmd/               # 應用程式進入點
│   ├── internal/          # 內部模組
│   │   ├── api/          # HTTP API 處理器
│   │   ├── scraper/      # 爬蟲核心 (parser.go 解析邏輯)
│   │   ├── storage/      # 資料儲存層 (batch.go 批次插入)
│   │   ├── service/      # 業務邏輯 (stock_service.go)
│   │   └── config/       # 配置管理
│   ├── pkg/              # 公開套件
│   ├── configs/          # 配置檔案
│   ├── deployments/      # 部署相關 (Dockerfile, docker-compose)
│   └── scripts/          # 建置與部署腳本
│
├── docs/                  # 專案文件
│   ├── README.md         # 文件索引
│   ├── QUICK_START.md    # 快速開始指南
│   └── crawler/          # 爬蟲詳細文檔
│
├── data/                  # 資料持久化 (gitignore)
│   └── postgres/         # PostgreSQL 資料目錄
│
├── logs/                  # 日誌輸出 (gitignore)
│
├── docker-compose.yml     # Docker Compose 配置
├── .env.example          # 環境變數範例
└── README.md             # 本檔案
```

---

## ⚙️ 配置說明

### 環境變數 (`.env`)

```bash
# 資料庫配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=stock_user
DB_PASSWORD=your_secure_password
DB_NAME=stock_analysis

# 爬蟲服務配置
CRAWLER_PORT=9627
MAX_WORKERS=20
CRAWLER_TIMEOUT=30
RETRY_ATTEMPTS=3
LOG_LEVEL=info
```

### 爬蟲配置 (`crawler-service/configs/config.yaml`)

```yaml
crawler:
  max_workers: 20          # 最大並發工作線程
  timeout: 30              # 請求超時時間 (秒)
  retry_attempts: 3        # 失敗重試次數
  delay: 100               # 請求間隔 (毫秒)
```

---

## 🔧 開發指南

### 本地運行

```bash
cd crawler-service

# 安裝依賴 (需要 Go 1.21+)
go mod download

# 編譯
go build -o bin/crawler cmd/crawler/main.go

# 執行
./bin/crawler
```

### 測試

```bash
# 執行所有測試
go test ./...

# 查看覆蓋率
go test -cover ./...
```

### 建置 Docker 映像檔

```bash
cd crawler-service
docker build -f deployments/Dockerfile -t stock-crawler-service:latest .
```

---

## 📊 監控與日誌

### 查看日誌

```bash
# 即時查看爬蟲日誌
docker-compose logs -f crawler-service

# 查看資料庫日誌
docker-compose logs -f postgres

# 查看最近 100 行
docker-compose logs --tail=100 crawler-service
```

### Prometheus 指標

重要指標：
- `crawler_tasks_total` - 總任務數
- `crawler_tasks_success_total` - 成功任務數
- `crawler_tasks_failure_total` - 失敗任務數
- `crawler_parse_duration_seconds` - 解析耗時
- `crawler_storage_duration_seconds` - 儲存耗時

---

## 🐛 故障排除

### 常見問題

#### 1. 容器無法啟動

```bash
# 查看日誌
docker-compose logs

# 重建並啟動
docker-compose down
docker-compose up -d --build
```

#### 2. 資料庫連線失敗

```bash
# 檢查資料庫狀態
docker-compose exec postgres psql -U stock_user -d stock_analysis -c "SELECT 1"

# 重啟資料庫
docker-compose restart postgres
```

#### 3. 爬取資料重複

**症狀**: 所有記錄顯示相同價格

**解決**: 已於 2026-01-11 修復 Go range loop 指標別名問題

詳見: [docs/crawler/CRAWLER_SERVICE.md](docs/crawler/CRAWLER_SERVICE.md#2-stock-service-層)

---

## 📚 完整文檔

- **[快速開始](docs/QUICK_START.md)** - 5 分鐘內啟動系統
- **[爬蟲服務完整指南](docs/crawler/CRAWLER_SERVICE.md)** - 架構、API、代碼走查
- **[部署指南](docs/crawler/DEPLOYMENT.md)** - 三種部署方式詳解
- **[API 文件](docs/crawler/API.md)** - RESTful API 完整說明
- **[Docker 指南](docs/crawler/DOCKER_GUIDE.md)** - Docker 使用與管理

---

## 🔄 維護與更新

### 停止服務

```bash
docker-compose down
```

### 更新服務

```bash
# 拉取最新代碼
git pull

# 重建並啟動
docker-compose up -d --build
```

### 資料庫備份

```bash
docker-compose exec postgres pg_dump -U stock_user stock_analysis > backup_$(date +%Y%m%d).sql
```

### 清理日誌

```bash
# 清理 30 天前的日誌
find logs -name "*.log" -mtime +30 -delete
```

---

## 🎯 效能指標

基於真實測試數據 (2026-01-11):

| 指標 | Go 爬蟲 | Python 爬蟲 (舊) | 提升 |
|------|---------|-----------------|------|
| 單股票爬取時間 | 10-15 秒 | 120-180 秒 | **10-12x** |
| 併發處理能力 | 1000+ goroutines | 50 threads | **20x** |
| 記憶體使用 | 50-100 MB | 300-500 MB | **70%↓** |
| CPU 使用率 | 20-40% | 80-100% | **60%↓** |

---

## 🆕 最近更新

### 2026-01-11
- ✅ 修復 Go range loop 指標別名問題 (股票 2330 資料重複)
- ✅ 專案重構：移除後端/前端，保留爬蟲核心服務
- ✅ 簡化 Docker Compose 配置 (只保留 postgres + crawler)
- ✅ 更新文檔結構與導航

---

## 📞 獲取幫助

- **文檔**: 查看 [docs/README.md](docs/README.md)
- **問題**: 提交 GitHub Issue
- **建議**: 提交 Pull Request

---

## 📄 授權

本專案為私有專案，未經授權請勿散布。

---

## 🙏 致謝

感謝所有貢獻者與使用者的支持！

---

**Made with ❤️ using Go**
