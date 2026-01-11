# 系統使用指南

本指南將說明如何使用股票分析系統的各項功能。

## 1. 基本功能

### 1.1 查詢股票資訊

#### 透過前端介面

1. 進入 http://localhost:3000
2. 點擊「股票」或「股票清單」
3. 您可以查看已爬取的股票清單
4. 點擊股票代碼可查看詳細資訊

#### 透過 API

```bash
# 獲取股票清單
curl http://localhost:9000/api/v1/stocks

# 獲取特定股票資訊
curl http://localhost:9000/api/v1/stocks/2330

# 獲取股票歷史資料
curl http://localhost:9000/api/v1/stocks/2330/history?days=30
```

### 1.2 爬取股票資料

#### 透過爬蟲儀表板

1. 進入 http://localhost:9627（爬蟲儀表板）
2. 在「測試爬取」區塊輸入股票代碼
3. 點擊「開始爬取」
4. 等待爬蟲完成

#### 透過 API

```bash
# 爬取單支股票
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'

# 批次爬取多支股票
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454"]}'
```

### 1.3 查看技術指標

#### 均線資料

```bash
# 獲取均線資訊
curl http://localhost:9000/api/v1/moving-averages/2330

# 指定時間範圍
curl http://localhost:9000/api/v1/moving-averages/2330?days=60
```

### 1.4 選股策略

```bash
# 完美多頭股票（MA5 > MA10 > MA20 > MA60 > MA120 > MA240）
curl http://localhost:9000/api/v1/stock-selection/perfect-uptrend

# 短線多頭股票（MA5 > MA10 > MA20）
curl http://localhost:9000/api/v1/stock-selection/short-uptrend

# 空頭股票
curl http://localhost:9000/api/v1/stock-selection/downtrend
```

## 2. 進階功能

### 2.1 定時更新

系統會自動在每日 14:00 更新股票資料。

手動觸發更新：

```bash
# 更新所有股票
curl -X POST "http://localhost:9000/api/v1/tasks/update-all-stocks"

# 更新均線資料
curl -X POST "http://localhost:9000/api/v1/tasks/update-moving-averages"
```

### 2.2 任務監控

1. 進入 Celery Flower: http://localhost:5555
2. 查看任務執行狀況
3. 檢查失敗的任務並查看錯誤訊息

### 2.3 資料庫管理

1. 進入 pgAdmin: http://localhost:9224
2. 登入帳號密碼：admin@admin.com / admin
3. 連接至 PostgreSQL 伺服器
4. 即可查看與管理資料

### 2.4 導出資料

```bash
# 導出 CSV 格式
curl http://localhost:9000/api/v1/stocks/2330/history/export \
  -H "Accept: text/csv" \
  --output stock_2330.csv

# 導出 JSON 格式
curl http://localhost:9000/api/v1/stocks/2330/history/export \
  -H "Accept: application/json" \
  --output stock_2330.json
```

## 3. 系統設定

### 3.1 修改爬蟲配置

編輯 `crawler-service/configs/config.yaml`：

```yaml
crawler:
  max_workers: 10              # 最大工作線程
  timeout: 30                  # 超時時間（秒）
  retry_attempts: 3            # 重試次數
  sources:                     # 數據來源
    - fubon
    - concord
```

### 3.2 修改後端配置

編輯 `backend/.env` 或環境變數：

```bash
DATABASE_URL=postgresql://user:password@localhost/stock_analysis
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
API_PORT=9000
```

### 3.3 修改定時任務

編輯 `backend/src/celery_app/config.py`：

```python
beat_schedule = {
    'update-stocks-daily': {
        'task': 'src.celery_app.tasks.update_all_stocks',
        'schedule': crontab(hour=14, minute=0),  # 每日 14:00
    },
}
```

## 4. 常見工作流程

### 工作流程 A：爬取新股票並分析

```bash
# 1. 爬取股票資料
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317"]}'

# 2. 等待 2-5 分鐘讓爬蟲完成

# 3. 更新均線資料
curl -X POST "http://localhost:9000/api/v1/tasks/update-moving-averages"

# 4. 查詢選股結果
curl http://localhost:9000/api/v1/stock-selection/perfect-uptrend

# 5. 檢視具體股票
curl http://localhost:9000/api/v1/stocks/2330/history
```

### 工作流程 B：批量更新所有股票

```bash
# 1. 獲取股票清單
curl http://localhost:9000/api/v1/stocks > stocks.json

# 2. 提取所有代碼並批次更新
cat stocks.json | jq -r '.[].code' | paste -sd ',' - | \
  xargs -I {} curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["{}"]}'

# 3. 監控進度
watch -n 5 'curl http://localhost:9627/metrics | grep crawler_tasks'
```

### 工作流程 C：性能分析與診斷

```bash
# 1. 檢查系統狀態
curl http://localhost:9000/health
curl http://localhost:9627/health

# 2. 檢查資料庫連線
docker-compose exec postgres psql -U stock_user -d stock_analysis -c "SELECT COUNT(*) FROM stock_daily_data;"

# 3. 查看爬蟲效能指標
curl http://localhost:9627/metrics

# 4. 檢查任務隊列
curl http://localhost:5555/api/tasks (Flower API)
```

## 5. 批量操作

### 批量爬取股票

```bash
# 方法 1：直接列表
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454", "2891", "3008"]}'

# 方法 2：從文件
SYMBOLS=$(cat stock_list.txt | paste -sd ',' -)
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d "{\"symbols\": [${SYMBOLS}]}"
```

### 批量更新均線

```bash
# 自動批次更新所有股票的均線
curl -X POST "http://localhost:9000/api/v1/tasks/update-moving-averages?batch_size=100"
```

## 6. 監控與日誌

### 查看實時日誌

```bash
# 所有服務
docker-compose logs -f

# 特定服務
docker-compose logs -f backend
docker-compose logs -f crawler-service
docker-compose logs -f postgres
```

### 效能監控

1. **Prometheus**: http://localhost:9090 (如已配置)
2. **Grafana**: http://localhost:3000/grafana (如已配置)
3. **Flower**: http://localhost:5555 (任務監控)

### 錯誤診斷

```bash
# 查看爬蟲錯誤
docker-compose logs crawler-service | grep ERROR

# 查看 API 錯誤
docker-compose logs backend | grep ERROR

# 查看資料庫錯誤
docker-compose logs postgres | grep ERROR
```

## 7. 備份與恢復

### 備份資料庫

```bash
docker-compose exec postgres pg_dump -U stock_user stock_analysis > backup.sql
```

### 恢復資料庫

```bash
docker-compose exec -T postgres psql -U stock_user stock_analysis < backup.sql
```

### 備份整個系統

```bash
docker-compose exec postgres pg_dump -U stock_user stock_analysis | \
  gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

## 8. 性能優化建議

1. **增加爬蟲工作線程**
   - 修改 `crawler-service/configs/config.yaml` 的 `max_workers`
   - 監控 CPU 和記憶體使用量

2. **調整資料庫連線池**
   - 修改 `backend/.env` 的 `DATABASE_POOL_SIZE`
   - 根據並發用戶數調整

3. **啟用快取**
   - Redis 自動快取 API 回應
   - 設定合適的 TTL 值

4. **定期清理日誌**
   ```bash
   docker-compose exec backend find /logs -name "*.log" -mtime +30 -delete
   ```

## 9. 故障排除

詳見 [故障排除指南](../troubleshooting/COMMON_ISSUES.md)

## 10. 更多資源

- [API 完整文件](../backend/API_DOCUMENTATION.md)
- [爬蟲服務指南](../crawler/CRAWLER_SERVICE.md)
- [開發指南](DEVELOPER_GUIDE.md)
- [專案結構](../PROJECT_STRUCTURE.md)
