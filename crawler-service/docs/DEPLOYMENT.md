# 部署指南

這份文檔提供三種部署方式，您可以根據需求選擇最適合的方式。

## 🚀 方式一：一鍵部署（推薦）

最簡單的方式，執行一個腳本就能完成所有設定。

### 使用方法

```bash
# 1. 進入專案目錄
cd crawler-service/

# 2. 執行一鍵部署腳本
./scripts/deploy.sh
```

### 互動式選單

腳本會顯示選單讓您選擇：

```
請選擇部署方式：
  1) Docker 部署（推薦）- 自動設定所有服務
  2) 本機部署 - 在本機直接執行
  3) 僅建構 - 只建構不執行
  4) 停止服務
  5) 查看日誌
  6) 健康檢查
  0) 退出
```

**推薦選擇 1 (Docker 部署)**，會自動：
- ✅ 檢查 Docker 環境
- ✅ 建立 .env 配置檔案
- ✅ 建構 Docker 映像
- ✅ 啟動所有服務（Go 爬蟲、PostgreSQL、Redis、Prometheus、Grafana）
- ✅ 顯示服務訪問資訊

---

## 🐳 方式二：Docker Compose 部署

如果您熟悉 Docker，可以直接使用 docker-compose。

### 前置需求

- Docker 20.10+
- docker-compose 1.29+

### 快速啟動

```bash
cd crawler-service/

# 1. 建立環境變數檔案
cp .env.example .env
# 編輯 .env 設定資料庫密碼等

# 2. 啟動所有服務
cd deployments/
docker-compose up -d

# 3. 查看服務狀態
docker-compose ps

# 4. 查看日誌
docker-compose logs -f crawler-service
```

### 停止服務

```bash
cd deployments/
docker-compose down
```

### 重新建構

```bash
cd deployments/
docker-compose build --no-cache
docker-compose up -d
```

---

## 💻 方式三：本機部署

在本機直接執行，適合開發和測試。

### 前置需求

- Go 1.21+
- PostgreSQL 15+
- Make（選配）

### 步驟

#### 1. 安裝 Go（如果未安裝）

```bash
# 執行自動安裝腳本
./scripts/install.sh
```

或手動安裝：

**Linux / WSL:**
```bash
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
```

**macOS:**
```bash
brew install go
```

#### 2. 設定環境變數

```bash
# 建立 .env 檔案
cp .env.example .env

# 編輯 .env
vim .env
```

重要配置：
```bash
DATABASE_URL=postgresql://stock_user:password@localhost:9221/stock_analysis
SERVER_PORT=8080
LOG_LEVEL=info
MAX_WORKERS=100
```

#### 3. 下載依賴和建構

```bash
# 下載依賴
go mod download
go mod tidy

# 建構
./scripts/build.sh
# 或
make build
```

#### 4. 啟動服務

```bash
# 使用啟動腳本（推薦）
./scripts/start.sh

# 或直接執行
export $(cat .env | xargs)
./bin/crawler-service
```

---

## 🔍 驗證部署

### 檢查健康狀態

```bash
# 健康檢查端點
curl http://localhost:8080/health

# 預期回應
{"status":"ok"}
```

### 檢查服務

```bash
# 如果使用 Docker
docker ps | grep stock-

# 如果使用本機部署
ps aux | grep crawler-service
```

### 查看日誌

**Docker:**
```bash
cd deployments/
docker-compose logs -f crawler-service
```

**本機:**
```bash
tail -f /var/log/crawler-service/app.log
# 或查看終端輸出
```

### 測試 API（當實作完成後）

```bash
# 測試爬取單支股票
curl http://localhost:8080/api/v1/stocks/2330/daily

# 測試批次更新
curl -X POST http://localhost:8080/api/v1/stocks/batch-update \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317"]}'
```

---

## 📊 訪問監控服務

部署完成後，可以訪問以下服務：

| 服務 | URL | 預設帳密 |
|-----|-----|---------|
| **Go 爬蟲服務** | http://localhost:8080 | - |
| **健康檢查** | http://localhost:8080/health | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin/admin |
| **PostgreSQL** | localhost:9221 | stock_user/password |
| **Redis** | localhost:9321 | - |

---

## 🛠 常見問題

### Q1: 提示 "port already in use"

**解決方法：** 修改 .env 檔案中的埠號

```bash
GO_CRAWLER_PORT=8081  # 改成其他埠號
```

### Q2: 資料庫連線失敗

**檢查步驟：**
```bash
# 1. 檢查資料庫是否運行
docker ps | grep postgres
# 或
sudo systemctl status postgresql

# 2. 測試連線
psql postgresql://stock_user:password@localhost:9221/stock_analysis

# 3. 檢查 DATABASE_URL 環境變數
echo $DATABASE_URL
```

### Q3: Docker 映像建構失敗

**解決方法：**
```bash
# 清理舊映像和容器
docker system prune -a

# 重新建構
cd deployments/
docker-compose build --no-cache
```

### Q4: Go 版本過舊

**解決方法：**
```bash
# 執行安裝腳本更新 Go
./scripts/install.sh
```

### Q5: 權限問題

**解決方法：**
```bash
# 給腳本加上執行權限
chmod +x scripts/*.sh

# 如果是資料庫連線問題，檢查 PostgreSQL 權限
sudo -u postgres psql
```

---

## 📦 更新部署

### 更新 Go 服務

```bash
# 1. 拉取最新程式碼
git pull

# 2. 重新建構
cd crawler-service/

# Docker 方式
cd deployments/
docker-compose build crawler-service
docker-compose up -d crawler-service

# 本機方式
./scripts/build.sh
./scripts/start.sh
```

### 更新配置

```bash
# 1. 修改 .env 檔案
vim .env

# 2. 重啟服務
# Docker
docker-compose restart crawler-service

# 本機
pkill crawler-service
./scripts/start.sh
```

---

## 🔒 生產環境建議

### 安全性

1. **修改預設密碼**
   ```bash
   # .env
   POSTGRES_PASSWORD=強密碼
   GRAFANA_PASSWORD=強密碼
   ```

2. **使用 HTTPS**
   - 配置反向代理（Nginx/Caddy）
   - 設定 SSL 證書

3. **限制網路訪問**
   - 只開放必要的埠號
   - 使用防火牆規則

### 效能優化

1. **調整 Worker 數量**
   ```bash
   # .env
   MAX_WORKERS=200  # 根據 CPU 核心數調整
   ```

2. **資料庫連線池**
   ```bash
   # .env
   DB_POOL_SIZE=50
   DB_MAX_IDLE=20
   ```

3. **資源限制**
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '4.0'
         memory: 2G
   ```

### 備份策略

1. **資料庫備份**
   ```bash
   # 定期備份
   docker exec stock-postgres pg_dump -U stock_user stock_analysis > backup.sql
   ```

2. **配置備份**
   ```bash
   # 備份配置檔案
   tar -czf config-backup.tar.gz .env configs/
   ```

---

## 📞 獲取幫助

如果遇到問題：

1. 查看日誌：`docker-compose logs -f` 或 `./scripts/deploy.sh` 選項 5
2. 健康檢查：`./scripts/deploy.sh` 選項 6
3. 查看文檔：
   - `QUICKSTART.md` - 快速開始
   - `docs/go-implementation-status.md` - 實施狀態
   - `docs/go-migration-plan.md` - 完整計劃

---

## 🎯 下一步

部署完成後：

1. **測試功能** - 執行健康檢查和 API 測試
2. **配置監控** - 訪問 Grafana 建立儀表板
3. **整合 Python** - 按照計劃整合到現有系統
4. **壓力測試** - 驗證效能是否達到預期

---

**祝部署順利！** 🚀
