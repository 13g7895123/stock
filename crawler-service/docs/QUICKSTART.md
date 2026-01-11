# 快速開始指南

這個指南將幫助您在 5 分鐘內啟動並執行 Go 爬蟲服務。

## 前置需求

- Go 1.21 或更高版本
- PostgreSQL 15+（或使用現有的資料庫）
- Make（選配，用於簡化命令）

## 安裝 Go（如果尚未安裝）

### Linux / WSL

```bash
# 下載 Go
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# 解壓到 /usr/local
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 設定環境變數
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# 驗證安裝
go version
```

### macOS

```bash
# 使用 Homebrew
brew install go

# 驗證安裝
go version
```

### Windows

下載並執行安裝程式：
https://go.dev/dl/go1.21.5.windows-amd64.msi

## 快速啟動

### 步驟 1：進入專案目錄

```bash
cd crawler-service/
```

### 步驟 2：下載依賴

```bash
go mod download
go mod tidy
```

### 步驟 3：配置環境變數

```bash
# 建立環境變數檔案
cat > .env << EOF
DATABASE_URL=postgresql://stock_user:password@localhost:9221/stock_analysis
SERVER_PORT=8080
LOG_LEVEL=info
MAX_WORKERS=100
EOF

# 載入環境變數
export $(cat .env | xargs)
```

### 步驟 4：建構應用程式

```bash
# 使用 make（推薦）
make build

# 或直接使用 go build
go build -o bin/crawler-service ./cmd/crawler/main.go
```

### 步驟 5：執行服務

```bash
# 使用 make（推薦）
make run

# 或直接執行
./bin/crawler-service
```

## 驗證服務

### 健康檢查

```bash
curl http://localhost:8080/health
# 預期回應: {"status":"ok"}
```

### 查看日誌

服務啟動時會顯示：
- 配置載入狀態
- 券商健康檢查結果
- 測試爬取結果（2330）
- HTTP 服務器監聽狀態

## 常用命令

### 開發

```bash
# 格式化程式碼
make fmt

# 執行程式碼檢查
make lint

# 執行測試
make test

# 產生覆蓋率報告
make test-coverage
```

### 建構

```bash
# 建構當前平台版本
make build

# 建構 Linux 版本
make build-linux
```

### Docker

```bash
# 建構 Docker 映像
make docker-build

# 執行 Docker 容器
make docker-run

# 停止容器
make docker-stop
```

## 常見問題

### Q: 提示 "go: command not found"

**A**: Go 尚未安裝或未加入 PATH。請參考上方的 "安裝 Go" 章節。

### Q: 提示 "database connection failed"

**A**: 檢查資料庫是否運行，以及 `DATABASE_URL` 環境變數是否正確。

```bash
# 檢查資料庫連線
psql postgresql://stock_user:password@localhost:9221/stock_analysis
```

### Q: 編譯錯誤 "package not found"

**A**: 執行 `go mod download` 下載所有依賴。

### Q: 埠號已被佔用

**A**: 修改配置檔案或環境變數中的 `SERVER_PORT`：

```bash
export SERVER_PORT=8081
```

## 下一步

### 開發

1. **實作資料庫模組**: 參考 `docs/go-implementation-status.md`
2. **實作 API 端點**: 參考 `docs/go-migration-plan.md`
3. **撰寫測試**: 參考 `tests/` 目錄

### 部署

1. **本地測試**: 使用 `make run` 在本地執行
2. **Docker 部署**: 使用 `make docker-compose-up` 啟動所有服務
3. **生產部署**: 參考 `docs/go-migration-plan.md` 的部署章節

## 有用的資源

- **完整文檔**: `docs/go-migration-plan.md`
- **實施狀態**: `docs/go-implementation-status.md`
- **API 文檔**: `docs/API.md`（待建立）
- **問題回報**: 請在 GitHub Issues 中回報

## 快速測試範例

```bash
# 1. 啟動服務
make run

# 2. 在另一個終端測試 API（當實作完成後）
curl http://localhost:8080/api/v1/stocks/2330/daily

# 3. 批次更新（當實作完成後）
curl -X POST http://localhost:8080/api/v1/stocks/batch-update \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454"]}'

# 4. 查看 Prometheus metrics（當實作完成後）
curl http://localhost:8080/metrics
```

## 獲取幫助

如果遇到問題：

1. 查看 `docs/go-implementation-status.md` 了解當前實施狀態
2. 查看 `docs/go-migration-plan.md` 了解完整計劃
3. 檢查日誌輸出
4. 在 GitHub Issues 中提問

---

**Happy Coding! 🚀**
