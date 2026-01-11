# 監控面板使用指南

## 📊 功能說明

已為 crawler-service 新增了一個簡易的 HTML 監控面板，可以即時查看已爬取的股票資料統計。

### 主要功能：

1. **統計卡片**
   - 總股票數
   - 總資料筆數
   - 平均筆數
   - 服務狀態（在線/離線）

2. **股票清單表格**
   - 顯示所有股票及其資料筆數
   - 包含起始日期、最新日期、資料來源

3. **互動功能**
   - 🔍 搜尋：依股票代碼或名稱搜尋
   - ⬆️⬇️ 排序：點擊表頭可排序（支援所有欄位）
   - 🔄 重新整理：手動更新資料
   - 📥 匯出 CSV：將資料匯出為 CSV 檔案
   - ⏱️ 自動更新：每 30 秒自動重新整理

## 🚀 啟動方式

### 方式 1：重新編譯並啟動（推薦）

```bash
# 1. 進入專案目錄
cd crawler-service

# 2. 重新編譯
make build
# 或
go build -o bin/crawler-service ./cmd/crawler/main.go

# 3. 啟動服務
./bin/crawler-service
# 或
make run
```

### 方式 2：使用 Docker 重新部署

```bash
# 1. 停止現有容器
docker-compose down

# 2. 重新建構並啟動
docker-compose up -d --build

# 3. 查看日誌確認啟動成功
docker-compose logs -f crawler-service
```

### 方式 3：使用部署腳本

```bash
cd crawler-service
./scripts/deploy.sh
# 選擇「1) Docker 部署」
```

## 🌐 訪問監控面板

服務啟動後，開啟瀏覽器訪問：

```
http://localhost:8080
```

**預設埠號：8080**（如果修改過配置，請使用對應的埠號）

### 其他端點：

- **監控面板**：http://localhost:8080/
- **健康檢查**：http://localhost:8080/health
- **統計 API**：http://localhost:8080/api/v1/stats/stocks-summary
- **Prometheus**：http://localhost:9090（如果啟用）
- **Grafana**：http://localhost:3001（如果啟用）

## ✅ 驗證安裝

### 1. 檢查服務是否正常運行

```bash
# 健康檢查
curl http://localhost:8080/health
# 應該返回：{"status":"healthy",...}
```

### 2. 檢查統計 API

```bash
# 獲取統計資料
curl http://localhost:8080/api/v1/stats/stocks-summary
# 應該返回 JSON 格式的股票統計資料
```

### 3. 開啟監控面板

在瀏覽器訪問 http://localhost:8080，應該會看到：
- ✅ 統計卡片顯示數據
- ✅ 股票清單表格
- ✅ 搜尋框和按鈕
- ✅ 服務狀態顯示「運行中」

## 🔧 故障排除

### 問題 1：無法訪問監控面板

**解決方法：**

1. 確認服務是否正在運行：
   ```bash
   # 檢查進程
   ps aux | grep crawler-service
   
   # 或檢查 Docker 容器
   docker ps | grep crawler
   ```

2. 檢查埠號是否正確：
   ```bash
   # 查看配置檔案
   cat configs/config.yaml | grep port
   ```

3. 確認防火牆設定：
   ```bash
   # Linux
   sudo ufw allow 8080
   ```

### 問題 2：頁面顯示「載入失敗」

**可能原因：**
- 資料庫未連接
- 沒有股票資料

**解決方法：**

1. 檢查資料庫連接：
   ```bash
   # 查看服務日誌
   docker-compose logs crawler-service
   # 或
   tail -f logs/crawler.log
   ```

2. 確認資料庫中有資料：
   ```bash
   # 連接資料庫
   psql postgresql://stock_user:password@localhost:9221/stock_analysis
   
   # 查詢股票數量
   SELECT COUNT(*) FROM stocks WHERE is_active = true;
   
   # 查詢資料筆數
   SELECT COUNT(*) FROM stock_daily_data;
   ```

3. 如果沒有資料，先爬取一些股票：
   ```bash
   curl -X POST http://localhost:8080/api/v1/stocks/batch-update \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["2330", "2317", "2454"]}'
   ```

### 問題 3：搜尋或排序不工作

**解決方法：**
- 清除瀏覽器快取（Ctrl + F5 或 Cmd + Shift + R）
- 檢查瀏覽器控制台是否有 JavaScript 錯誤（F12）

### 問題 4：服務狀態顯示「離線」

**解決方法：**
1. 檢查 API 是否可訪問：
   ```bash
   curl http://localhost:8080/api/v1/stats/stocks-summary
   ```

2. 如果 API 無法訪問，檢查 CORS 設定（如果跨域訪問）

## 📝 進階配置

### 修改自動更新間隔

編輯 `web/index.html`，找到這一行：

```javascript
// 每 30 秒自動更新
setInterval(loadData, 30000);
```

將 `30000`（毫秒）改為你想要的間隔。

### 修改顯示樣式

所有樣式都在 `web/index.html` 的 `<style>` 標籤內，可自行調整：
- 顏色主題
- 字體大小
- 卡片佈局

### 新增欄位

如果要新增更多統計資訊：

1. 修改後端 SQL 查詢（`internal/storage/repository.go`）
2. 更新 HTML 表格欄位（`web/index.html`）

## 📊 使用技巧

### 1. 快速找到特定股票
在搜尋框輸入股票代碼或名稱（支援部分匹配）

### 2. 找出資料最多的股票
點擊「資料筆數」欄位標題，降序排列

### 3. 查看最近更新的股票
點擊「最新日期」欄位標題，降序排列

### 4. 匯出資料供 Excel 分析
點擊「📥 匯出 CSV」按鈕，會下載 CSV 檔案

## 🎯 下一步

監控面板已經可以使用了！你可以：

1. ✅ 查看已爬取的股票資料統計
2. ✅ 監控資料更新狀態
3. ✅ 匯出資料進行分析

如果需要更進階的功能（如圖表、即時推送、歷史趨勢等），建議使用 Vue 或 React 來開發更完整的前端應用。

## 🆘 需要幫助？

如有問題，請檢查：
1. 服務日誌：`docker-compose logs -f crawler-service`
2. 瀏覽器控制台（F12）
3. API 回應：`curl http://localhost:8080/api/v1/stats/stocks-summary`

---

**祝您使用愉快！** 🎉
