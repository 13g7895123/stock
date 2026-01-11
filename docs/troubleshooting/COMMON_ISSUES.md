# 常見問題與故障排除指南

## 🚀 啟動與部署相關

### Q1: 容器無法啟動

**症狀**: `docker-compose up` 後容器立即退出或持續重啟

**解決步驟**:

1. **查看詳細錯誤訊息**
```bash
docker-compose logs --tail=50
# 或查看特定服務
docker-compose logs backend
docker-compose logs crawler-service
```

2. **清理並重新建置**
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

3. **檢查磁碟空間**
```bash
df -h
# 如果 /var/lib/docker 空間不足，執行清理
docker image prune -a
docker volume prune
```

4. **驗證環境變數**
```bash
# 檢查 .env 檔案
cat .env

# 確認變數格式正確（無引號、無空格）
DATABASE_URL=postgresql://user:password@postgres:5432/stock_analysis
```

### Q2: 端口被佔用

**症狀**: `Error response from daemon: driver failed programming external connectivity`

**解決方案**:

```bash
# 找出佔用端口的程序（以 3000 為例）
lsof -i :3000

# 終止程序
kill -9 <PID>

# 或修改 docker-compose.yml 的 ports 設定
# 將 "3000:3000" 改為 "3001:3000"
```

### Q3: Docker daemon 不運行

**症狀**: `Cannot connect to Docker daemon`

**解決方案**:

```bash
# 啟動 Docker（Linux）
sudo systemctl start docker

# 或重新啟動（macOS/Windows）
# 在應用程式中開啟 Docker Desktop

# 驗證 Docker 運行
docker --version
docker ps
```

## 📊 資料庫相關

### Q4: 資料庫連線失敗

**症狀**: `connection refused` 或 `authentication failed`

**檢查清單**:

1. **驗證資料庫容器是否運行**
```bash
docker-compose ps postgres

# 狀態應為 "Up"
# 如未啟動：
docker-compose up -d postgres
sleep 10  # 等待初始化
```

2. **檢查連線設定**
```bash
# 查看環境變數
echo $DATABASE_URL

# 驗證正確格式
# postgresql://username:password@host:port/dbname
```

3. **測試連線**
```bash
# 進入 postgres 容器測試連線
docker-compose exec postgres psql -U stock_user -d stock_analysis -c "SELECT 1"

# 從主機測試（需裝 psql）
psql postgresql://stock_user:password@localhost:9222/stock_analysis -c "SELECT 1"
```

4. **查看資料庫日誌**
```bash
docker-compose logs postgres | tail -50
```

5. **重啟資料庫**
```bash
docker-compose restart postgres
sleep 15
```

### Q5: 資料庫初始化失敗

**症狀**: 無 `stock_daily_data` 表或其他表缺失

**解決方案**:

```bash
# 1. 檢查遷移狀態
docker-compose exec backend alembic current

# 2. 執行遷移
docker-compose exec backend alembic upgrade head

# 3. 驗證表存在
docker-compose exec postgres psql -U stock_user -d stock_analysis -c "\dt"

# 如仍然失敗，執行初始化 SQL
docker-compose exec -T postgres psql -U stock_user stock_analysis < backend/sql/init.sql
```

### Q6: 磁碟空間滿導致資料庫故障

**症狀**: `No space left on device` 錯誤

**解決方案**:

```bash
# 檢查磁碟使用量
df -h

# 查看 Docker 資料卷大小
docker system df

# 清理舊日誌
docker-compose exec postgres \
  find /var/log/postgresql -name "*.log" -mtime +30 -delete

# 清理容器產生的垃圾
docker system prune

# 清理所有未使用資源
docker system prune -a
```

## 🔍 爬蟲服務相關

### Q7: 爬蟲資料全部重複

**症狀**: 股票 2330 所有記錄顯示相同 open/high/low/close (1665/1700/1655/1680)

**原因**: Go range loop 指標別名 bug（已於 2026-01-11 修復）

**驗證是否已修復**:

```bash
# 查詢資料是否有變動
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT DISTINCT open_price, close_price FROM stock_daily_data WHERE stock_code = '2330' LIMIT 5;"

# 結果應顯示多個不同值，如：
# open_price | close_price
# -----------+-------------
#     293.71 |      293.71
#     287.50 |      285.29
#     285.73 |      289.28
```

**如果仍未修復**:

```bash
# 1. 確認代碼已更新
docker-compose logs crawler-service | grep "range loop"

# 2. 重新建置映像檔
cd crawler-service
docker build -f deployments/Dockerfile -t stock-crawler-service:latest .

# 3. 重啟服務
docker-compose down crawler-service
docker-compose up -d crawler-service

# 4. 清空資料並重新爬取
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis \
  -c "TRUNCATE TABLE stock_daily_data;"

# 5. 重新爬取
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'

sleep 20

# 6. 驗證結果
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT open_price, close_price FROM stock_daily_data WHERE stock_code = '2330' LIMIT 10 ORDER BY trade_date;"
```

### Q8: 爬蟲超時

**症狀**: 爬蟲任務經常失敗，提示 "timeout" 或 "context deadline"

**解決方案**:

1. **增加超時時間**
```yaml
# crawler-service/configs/config.yaml
crawler:
  timeout: 60  # 從 30 增加到 60 秒
```

2. **減少併發以避免過載**
```yaml
crawler:
  max_workers: 10  # 從 20 減少到 10
```

3. **檢查網路連線**
```bash
# 測試連線到券商網站
curl -I https://fubon-ebrokerdj.fbs.com.tw

# 檢查 DNS 解析
nslookup fubon-ebrokerdj.fbs.com.tw
```

4. **查看爬蟲日誌**
```bash
docker-compose logs crawler-service | grep -i timeout
```

### Q9: 爬蟲資料不完整（少於 1440 筆）

**症狀**: 爬取後只有部分資料

**檢查步驟**:

```bash
# 1. 查看記錄數
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT COUNT(*) FROM stock_daily_data WHERE stock_code = '2330';"

# 2. 查看日期範圍
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis -c \
  "SELECT MIN(trade_date), MAX(trade_date) FROM stock_daily_data WHERE stock_code = '2330';"

# 3. 檢查爬蟲日誌
docker-compose logs crawler-service | grep "2330"

# 4. 如果少於 1440 筆，檢查券商 API 回應
# 在爬蟲代碼中新增 debug log
```

### Q10: 爬蟲持續報告資料庫錯誤

**症狀**: 
```
Error: failed to insert stock data: connection refused
```

**解決方案**:

1. **檢查資料庫連線**
```bash
docker-compose exec crawler-service \
  nc -zv postgres 5432
```

2. **檢查爬蟲環境變數**
```bash
docker-compose config | grep -A 5 crawler-service
```

3. **查看爬蟲詳細日誌**
```bash
docker-compose logs -f crawler-service --tail=100
```

4. **重啟爬蟲服務**
```bash
docker-compose restart crawler-service
```

## 🔌 API 相關

### Q11: API 請求返回 500 錯誤

**症狀**: 
```json
{"status": 500, "message": "Internal Server Error"}
```

**解決步驟**:

1. **查看後端日誌**
```bash
docker-compose logs backend | grep ERROR | tail -20
```

2. **檢查資料庫連線**
```bash
curl http://localhost:9000/health
```

3. **查看詳細日誌**
```bash
docker-compose logs backend --tail=100
```

4. **重啟後端服務**
```bash
docker-compose restart backend
```

### Q12: API 回應遲緩

**症狀**: API 請求耗時超過 5 秒

**優化建議**:

1. **啟用快取**
```bash
# 檢查 Redis 是否運行
docker-compose ps redis

# 測試 Redis 連線
docker-compose exec redis redis-cli ping
```

2. **檢查資料庫查詢效能**
```bash
# 進入資料庫檢查索引
docker-compose exec postgres psql -U stock_user -d stock_analysis

# 檢查索引
\d+ stock_daily_data

# 如果缺少索引，建立
CREATE INDEX idx_stock_code_date ON stock_daily_data(stock_code, trade_date);
```

3. **限制回傳筆數**
```bash
# 使用分頁而非一次返回所有資料
curl "http://localhost:9000/api/v1/stocks/2330/history?limit=100&offset=0"
```

### Q13: API 認證失敗

**症狀**: 
```
{"status": 401, "message": "Unauthorized"}
```

**解決方案**:

```bash
# 檢查 API 金鑰
echo $API_KEY

# 確認請求中包含正確的認證頭
curl -H "Authorization: Bearer $API_KEY" http://localhost:9000/api/v1/stocks
```

## 🧪 測試相關

### Q14: 測試無法執行

**症狀**: `pytest` 或 `go test` 命令失敗

**解決方案**:

```bash
# 後端測試
cd backend

# 確保測試資料庫存在
pytest --setup-show -v

# 檢查測試日誌
pytest -v -s | tail -50

# Go 爬蟲測試
cd crawler-service
go test -v ./...
```

### Q15: 測試資料庫連線失敗

**症狀**: 測試無法連接測試資料庫

**解決方案**:

```bash
# 確保測試資料庫配置正確
cat conftest.py | grep DATABASE

# 手動建立測試資料庫
docker-compose exec postgres createdb -U stock_user test_stock_analysis

# 重新執行測試
pytest -v
```

## 📝 日誌與監控

### Q16: 日誌文件太大

**症狀**: `/logs` 目錄佔用大量空間

**清理方案**:

```bash
# 查看日誌大小
du -sh logs/*

# 刪除 30 天前的日誌
find logs -name "*.log" -mtime +30 -delete

# 或定期執行清理（添加至 crontab）
0 3 * * * find /home/jarvis/project/idea/stock/logs -name "*.log" -mtime +30 -delete
```

### Q17: 無法找到監控圖表

**症狀**: Prometheus 或 Grafana 無法存取

**檢查**:

```bash
# 確認 Prometheus 容器運行
docker-compose ps prometheus

# 檢查 Grafana 容器
docker-compose ps grafana

# 訪問 Prometheus
curl http://localhost:9090

# 訪問 Grafana
curl http://localhost:3000
```

## 🆘 進階問題

### Q18: 應用程式記憶體持續增長

**症狀**: 應用運行一段時間後 OOM (Out of Memory)

**診斷**:

```bash
# 監控容器記憶體使用
docker stats

# 查看爬蟲記憶體使用
docker exec crawler-service ps aux
```

**解決方案**:

1. 減少 `max_workers`
2. 新增記憶體限制至 docker-compose.yml
3. 實施定期重啟

### Q19: 資料同步不一致

**症狀**: 同一股票在不同 API 取得的資料不一致

**檢查**:

```bash
# 比較資料庫與外部 API 資料
curl https://api.example.com/stock/2330 > external.json
curl http://localhost:9000/api/v1/stocks/2330 > internal.json

# 比對差異
diff external.json internal.json
```

## 📞 獲取幫助

如問題未能解決，請提供以下資訊：

1. **詳細錯誤訊息**
```bash
docker-compose logs --all > logs.txt
```

2. **系統資訊**
```bash
docker --version
docker-compose --version
uname -a
```

3. **配置資訊**
```bash
docker-compose config
```

4. **相關命令的執行結果**

5. **時間線** - 問題發生的時間點和前後操作

## 更多資源

- [快速開始](../guides/QUICK_START.md)
- [使用指南](../guides/USAGE_GUIDE.md)
- [爬蟲服務指南](../crawler/CRAWLER_SERVICE.md)
- [API 文件](../backend/API_DOCUMENTATION.md)
