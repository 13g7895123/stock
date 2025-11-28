# 股票分析系統使用說明 (Stock Analysis System Guide)

本系統整合了 Vue 前端、Python 後端 API、Go 高效能爬蟲服務以及 PostgreSQL 資料庫。以下是啟動與使用指南。

## 1. 快速啟動 (Quick Start)

確保您已安裝 Docker 與 Docker Compose。

在專案根目錄執行以下指令以啟動所有服務：

```bash
docker compose up -d --build
```

此指令會自動建置前端、後端與爬蟲服務的 Docker 映像檔並啟動容器。

## 2. 服務存取 (Access Points)

啟動後，您可以透過瀏覽器存取以下服務：

| 服務名稱 | 網址 | 說明 |
|---------|------|------|
| **前端介面 (Frontend)** | **http://localhost:3000** | 主要操作介面 (Vue/Nuxt) |
| **後端 API 文件 (Backend)** | http://localhost:8000/docs | Python FastAPI Swagger 文件 |
| **Go 爬蟲服務 (Crawler)** | http://localhost:8082/health | 爬蟲服務健康狀態 |
| **PgAdmin (資料庫管理)** | http://localhost:9627 | PostgreSQL 圖形化管理介面 |
| **Celery Flower** | http://localhost:5555 | 背景任務監控 |

## 3. 功能使用指南 (Feature Guide)

### 3.1 Go 爬蟲服務儀表板 (Crawler Dashboard)

這是本次更新的核心功能，用於監控與操作 Go 語言編寫的高效能爬蟲。

1. 進入前端首頁 **http://localhost:3000**。
2. 點擊左側選單的 **Go 爬蟲服務** -> **服務儀表板**。
3. 您可以在此頁面看到：
   - **服務狀態**：爬蟲服務是否在線。
   - **資料庫連線**：是否成功連線至 PostgreSQL。
   - **券商健康度**：各個資料來源網站的連線狀況。

### 3.2 測試爬取功能 (Testing Crawler)

在儀表板下方有兩個測試區塊：

**A. 單一股票爬取測試**
1. 輸入股票代碼 (例如 `2330`)。
2. 點擊「開始爬取」。
3. 系統會即時呼叫 Go 爬蟲抓取該股票的日線資料並寫入資料庫。
4. 成功後會顯示耗時與資料筆數。

**B. 批次股票爬取測試**
1. 輸入多個股票代碼，以逗號分隔 (例如 `2330,2317,2454`)。
2. 點擊「批次爬取」。
3. 系統會啟動並發爬蟲同時抓取這些股票。

### 3.3 查看股票資料 (View Stock Data)

爬取完成後，您可以查看資料是否已存入：

1. 點擊左側選單的 **股票管理** -> **股票清單**。
2. 此列表會顯示資料庫中已存在的股票。
3. 您可以看到股票的代碼、名稱、市場別等資訊。

## 4. 常見問題與故障排除 (Troubleshooting)

### 服務無法啟動？
檢查 Docker 日誌以了解錯誤原因：

```bash
# 查看所有服務日誌
docker compose logs -f

# 查看特定服務日誌 (例如爬蟲服務)
docker compose logs -f crawler-service
```

### 資料庫連線失敗？
請確認 `docker-compose.yml` 中的資料庫帳號密碼設定是否與您的環境變數一致。預設為：
- User: `stock_user`
- Password: `password`
- DB Name: `stock_analysis`

### 端口衝突？
如果啟動時提示端口被佔用 (例如 3000 或 8080)，請修改 `docker-compose.yml` 中的 `ports` 對應設定，或關閉佔用端口的本機服務。

## 5. 開發資訊 (Development Info)

- **前端 (Frontend)**: 位於 `frontend/` 目錄，使用 Vue 3 + Nuxt 3。
- **爬蟲服務 (Crawler)**: 位於 `crawler-service/` 目錄，使用 Go 語言。
- **後端 (Backend)**: 位於 `backend/` 目錄，使用 Python FastAPI。
