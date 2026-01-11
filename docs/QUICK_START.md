# 快速開始指南 - Stock Crawler Service

> 5 分鐘內啟動高效能股票爬蟲服務

## 前置需求

- **Docker** 20.10+
- **Docker Compose** 1.29+
- （可選）Go 1.21+ 用於本地開發

## 🚀 快速啟動

### 1. 克隆專案

```bash
git clone https://github.com/13g7895123/stock.git
cd stock
```

### 2. 設定環境變數

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 設定密碼（可選）
nano .env
```

**建議修改的變數：**
```bash
DB_PASSWORD=your_secure_password_here  # 修改資料庫密碼
```

### 3. 啟動服務

```bash
# 啟動所有服務（PostgreSQL + 爬蟲服務）
docker-compose up -d

# 等待服務啟動（約 15-20 秒）
sleep 20

# 查看服務狀態
docker-compose ps
```

**預期輸出：**
```
NAME                      STATUS          PORTS
crawler_postgres          Up (healthy)    0.0.0.0:9222->5432/tcp
stock_crawler_dashboard   Up (healthy)    0.0.0.0:9627->8082/tcp
```

### 4. 驗證安裝

```bash
# 檢查爬蟲服務健康狀態
curl http://localhost:9627/health
```

**預期回應：**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

---

## 📊 首次使用

### 爬取第一支股票 (以台積電 2330 為例)

```bash
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_1768117170",
    "total_symbols": 1,
    "started_at": "2026-01-11T10:00:00Z",
    "status": "processing",
    "message": "Submitted 1 tasks successfully"
  }
}
```

### 等待爬蟲完成

```bash
# 等待約 10-30 秒（取決於資料量）
sleep 20

# 查看日誌
docker-compose logs -f crawler-service
```

### 驗證資料

```bash
# 查詢資料庫
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT stock_code, trade_date, open_price, close_price FROM stock_daily_data WHERE stock_code = '2330' ORDER BY trade_date LIMIT 10;"
```

**預期輸出：**
```
 stock_code | trade_date | open_price | close_price 
------------+------------+------------+-------------
 2330       | 2020-02-17 |     293.71 |      293.71
 2330       | 2020-02-18 |     287.50 |      285.29
 2330       | 2020-02-19 |     285.73 |      289.28
 ...
```

---

## 🔍 常用操作

### 批次爬取多支股票

```bash
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454", "2891"]}'
```

### 查詢股票列表

```bash
curl http://localhost:9627/api/v1/stocks
```

### 查看系統指標

```bash
curl http://localhost:9627/metrics
```

### 查看服務日誌

```bash
# 即時查看爬蟲日誌
docker-compose logs -f crawler-service

# 查看最近 100 行
docker-compose logs --tail=100 crawler-service

# 查看資料庫日誌
docker-compose logs postgres
```

---

## ⚙️ 服務管理

### 停止服務

```bash
docker-compose down
```

### 重啟服務

```bash
docker-compose restart
```

### 完全重建

```bash
# 停止並移除容器
docker-compose down

# 重新建置並啟動
docker-compose up -d --build
```

### 查看資源使用

```bash
docker stats
```

---

## 🐛 常見問題

### 1. 容器無法啟動

```bash
# 查看詳細日誌
docker-compose logs

# 檢查端口是否被佔用
lsof -i :9627
lsof -i :9222

# 完全清理後重試
docker-compose down -v
docker-compose up -d
```

### 2. 資料庫連線失敗

```bash
# 檢查資料庫狀態
docker-compose ps postgres

# 查看資料庫日誌
docker-compose logs postgres

# 重啟資料庫
docker-compose restart postgres
sleep 10
```

### 3. 爬蟲服務無法訪問

```bash
# 檢查服務狀態
docker-compose ps crawler-service

# 查看爬蟲日誌
docker-compose logs crawler-service

# 測試健康檢查
curl -v http://localhost:9627/health
```

### 4. 權限問題（uploads 目錄）

```bash
# 修改權限
sudo chown -R $USER:$USER uploads/
```

---

## 📚 下一步

完成快速開始後，您可以：

1. **深入了解爬蟲服務**  
   查看 [爬蟲服務完整指南](crawler/CRAWLER_SERVICE.md)

2. **學習 API 使用**  
   查看 [API 文件](crawler/API.md)

3. **部署到生產環境**  
   查看 [部署指南](crawler/DEPLOYMENT.md)

4. **監控與優化**  
   查看 [Docker 指南](crawler/DOCKER_GUIDE.md)

---

## 🎯 配置調整

### 修改爬蟲參數

編輯 `.env` 檔案：

```bash
# 增加並發數（預設 20）
MAX_WORKERS=50

# 增加超時時間（預設 30 秒）
CRAWLER_TIMEOUT=60

# 增加重試次數（預設 3）
RETRY_ATTEMPTS=5
```

重啟服務使配置生效：

```bash
docker-compose restart crawler-service
```

### 修改資料庫端口

編輯 `.env` 檔案：

```bash
DB_PORT=5432  # 改為其他端口
```

重啟服務：

```bash
docker-compose down
docker-compose up -d
```

---

## 📞 獲取幫助

- 查看 [完整文檔](README.md)
- 查看 [常見問題](crawler/CRAWLER_SERVICE.md#-常見問題)
- 提交 [GitHub Issue](https://github.com/13g7895123/stock/issues)

---

**恭喜！您已成功啟動股票爬蟲服務 🎉**
