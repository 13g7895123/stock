# 快速開始指南 (Quick Start)

> 5 分鐘內啟動完整的股票分析系統

## 前置需求

- **Docker** 20.10+ 與 **Docker Compose** 1.29+
- （可選）Python 3.11+、Node.js 20+、Go 1.21+

## 🚀 一鍵啟動（推薦）

在專案根目錄執行：

```bash
docker-compose up -d
```

等待所有容器啟動完成（約 30-60 秒）：

```bash
docker-compose ps
```

確認所有服務都顯示 `Up`。

## 📍 服務存取

啟動後，您可以透過以下網址存取服務：

| 服務 | 網址 | 說明 |
|------|------|------|
| **前端** | http://localhost:3000 | Vue/Nuxt 主應用 |
| **API 文件** | http://localhost:9000/docs | FastAPI Swagger 文件 |
| **爬蟲儀表板** | http://localhost:9627 | Go 爬蟲監控介面 |
| **資料庫管理** | http://localhost:9224 | pgAdmin 資料庫工具 |
| **任務監控** | http://localhost:5555 | Celery Flower |

## 🔍 驗證安裝

### 1. 檢查服務健康狀態

```bash
# 檢查後端健康狀態
curl http://localhost:9000/health

# 檢查爬蟲服務健康狀態
curl http://localhost:9627/health
```

### 2. 查看服務日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f backend
docker-compose logs -f crawler-service
docker-compose logs -f frontend
```

## 📊 首次使用步驟

### 1. 建立資料庫

```bash
# 執行資料庫遷移
docker-compose exec backend python -m alembic upgrade head
```

### 2. 爬取股票資料

```bash
# 爬取單支股票資料（以 2330 為例）
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'

# 查看爬蟲進度
curl http://localhost:9627/metrics
```

### 3. 查看資料

```bash
# 查詢股票列表
curl http://localhost:9000/api/v1/stocks

# 查詢特定股票歷史資料
curl http://localhost:9000/api/v1/stocks/2330/history
```

## ⚙️ 常見操作

### 停止服務

```bash
docker-compose down
```

### 完全重啟（清空資料）

```bash
docker-compose down -v
docker-compose up -d
```

### 查看特定服務日誌

```bash
# 查看後端日誌
docker-compose logs -f backend --tail=100

# 查看爬蟲日誌
docker-compose logs -f crawler-service --tail=100

# 查看資料庫日誌
docker-compose logs -f postgres --tail=50
```

### 進入容器執行命令

```bash
# 進入後端容器
docker-compose exec backend bash

# 進入爬蟲容器
docker-compose exec crawler-service bash

# 進入資料庫容器
docker-compose exec postgres psql -U stock_user -d stock_analysis
```

## 🐛 故障排除

### 容器無法啟動

```bash
# 檢查完整日誌
docker-compose logs --all

# 重建映像檔
docker-compose build --no-cache

# 重新啟動
docker-compose down
docker-compose up -d
```

### 資料庫連線失敗

```bash
# 檢查資料庫狀態
docker-compose ps postgres

# 重啟資料庫
docker-compose restart postgres

# 查看資料庫日誌
docker-compose logs postgres
```

### 端口被佔用

檢查並終止佔用的程序：

```bash
# 尋找佔用端口的程序（以 3000 為例）
lsof -i :3000

# 終止程序
kill -9 <PID>
```

## 📚 後續步驟

- 閱讀 [使用指南](USAGE_GUIDE.md) 了解各項功能
- 查閱 [API 文件](../backend/API_DOCUMENTATION.md) 
- 檢查 [爬蟲服務指南](../crawler/CRAWLER_SERVICE.md)
- 查看 [專案結構](../PROJECT_STRUCTURE.md)

## 💡 提示

- 第一次爬取股票資料可能需要 1-5 分鐘（取決於資料量）
- 可以在 Celery Flower 介面監控後台任務執行情況
- 使用 `docker-compose ps` 隨時查看服務狀態
- 日誌文件位於各服務容器內的 `/logs/` 目錄

## 需要幫助？

- 遇到問題？查看 [故障排除指南](../troubleshooting/COMMON_ISSUES.md)
- 開發相關問題？參考 [開發指南](DEVELOPER_GUIDE.md)
- API 使用問題？檢視 [API 文件](../backend/API_DOCUMENTATION.md)
