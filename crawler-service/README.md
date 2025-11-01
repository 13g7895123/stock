# 股票爬蟲服務 (Go)

高效能的台灣股票資料爬蟲服務，使用 Go 語言實作，支援從 8 個券商網站爬取股票日線資料。

## 特性

- ⚡ **高效能**: 相比 Python 版本提升 10-20 倍效能
- 🚀 **高併發**: 支援 1000+ Goroutines 並發處理
- 💾 **低資源**: 記憶體使用降低 60-80%
- 📦 **易部署**: 單一執行檔，無依賴問題
- 📊 **可監控**: 整合 Prometheus + Grafana
- 🔄 **容錯性**: 多資料源輪詢，自動重試

## 架構

```
crawler-service/
├── cmd/                    # 應用程式入口
├── internal/               # 內部套件
│   ├── config/            # 配置管理
│   ├── scraper/           # 爬蟲核心
│   ├── storage/           # 資料儲存
│   ├── worker/            # 併發處理
│   ├── api/               # API 處理器
│   └── metrics/           # 監控指標
├── pkg/                   # 公共套件
├── tests/                 # 測試
├── configs/               # 配置檔案
└── deployments/           # 部署配置
```

## 快速開始

### 🚀 一鍵啟動（推薦）

**最簡單的方式，只需一個命令！**

```bash
cd crawler-service/
./scripts/deploy.sh
```

選擇「1) Docker 部署」即可自動完成所有設定和啟動。

### 📦 三種部署方式

我們提供三種部署方式，選擇最適合您的：

1. **一鍵部署** - 執行 `./scripts/deploy.sh`，互動式選單
2. **Docker Compose** - `cd deployments && docker-compose up -d`
3. **本機執行** - `./scripts/install.sh && ./scripts/start.sh`

詳細說明請參考：
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 完整部署指南
- **[QUICKSTART.md](QUICKSTART.md)** - 5 分鐘快速開始

### 前置需求（僅本機執行需要）

- Go 1.21+（可用 `./scripts/install.sh` 自動安裝）
- PostgreSQL 15+
- Make（選配）

如果使用 Docker 部署，只需要：
- Docker 20.10+
- docker-compose 1.29+

### 配置

複製並編輯配置檔案：

```bash
cp configs/config.yaml configs/config.local.yaml
# 編輯 config.local.yaml，設定資料庫連線等
```

### 執行

```bash
# 開發模式
make run

# 生產模式
./bin/crawler-service
```

### 測試

```bash
# 執行所有測試
make test

# 僅執行單元測試
make test-unit

# 產生覆蓋率報告
make test-coverage
```

## API 端點

### 健康檢查

```bash
GET /api/v1/health
```

### 爬取單一股票資料

```bash
GET /api/v1/stocks/:symbol/daily

# 範例
curl http://localhost:8080/api/v1/stocks/2330/daily
```

### 批次更新股票資料

```bash
POST /api/v1/stocks/batch-update
Content-Type: application/json

{
  "symbols": ["2330", "2317", "2454"]
}
```

### 查詢歷史資料

```bash
GET /api/v1/stocks/:symbol/history?start=2024-01-01&end=2024-12-31
```

### Prometheus Metrics

```bash
GET /metrics
```

## Docker 部署

### 建構映像

```bash
make docker-build
```

### 執行容器

```bash
make docker-run
```

### 使用 docker-compose

```bash
# 啟動所有服務
make docker-compose-up

# 停止所有服務
make docker-compose-down
```

## 效能指標

| 指標 | Python | Go | 提升 |
|-----|--------|-----|------|
| 批次處理速度 | ~10 stocks/sec | 100-200 stocks/sec | 10-20x |
| 並發處理能力 | 4-8 threads | 1000+ goroutines | 100x+ |
| 記憶體使用 | ~500MB | ~100MB | 5x |
| 映像大小 | ~500MB | ~20MB | 25x |

## 開發

### 程式碼格式化

```bash
make fmt
```

### 程式碼檢查

```bash
make lint
```

### 安裝開發工具

```bash
make install-tools
```

## 監控

服務整合了 Prometheus metrics，可以使用 Grafana 建立儀表板。

### 關鍵指標

- `crawler_requests_total` - 總請求數
- `crawler_request_duration_seconds` - 請求延遲
- `crawler_fetch_requests_total` - 爬蟲請求總數
- `crawler_success_rate` - 成功率
- `db_operation_duration_seconds` - 資料庫操作延遲

## 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `SERVER_PORT` | 服務埠號 | 8080 |
| `DATABASE_URL` | 資料庫連線字串 | - |
| `LOG_LEVEL` | 日誌等級 | info |
| `MAX_WORKERS` | 最大併發數 | 100 |

## 故障排查

### 查看日誌

```bash
# Docker
make logs

# 本機
tail -f /var/log/crawler-service/app.log
```

### 健康檢查

```bash
curl http://localhost:8080/api/v1/health
```

### 常見問題

**Q: 資料庫連線失敗**
A: 檢查 `DATABASE_URL` 環境變數，確保資料庫可訪問。

**Q: 記憶體使用過高**
A: 調整 `MAX_WORKERS` 參數，降低併發數量。

**Q: 爬取失敗**
A: 檢查券商網站是否可訪問，查看日誌了解詳細錯誤。

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License

## 相關連結

- [Go 遷移計劃](../docs/go-migration-plan.md)
- [API 文檔](./docs/API.md)
- [架構說明](./docs/ARCHITECTURE.md)
