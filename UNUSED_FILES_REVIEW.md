# 未使用檔案清單 - 建議刪除檢視

此文件列出專案中可能未使用或可以清理的檔案和目錄，請仔細檢視後決定是否刪除。

## 🚨 確定可以刪除的檔案

### Python 編譯和快取檔案
```bash
# 所有 __pycache__ 目錄和 .pyc 檔案
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# pytest 快取
backend/.pytest_cache/

# 特定快取目錄
backend/src/api/endpoints/__pycache__/
backend/src/api/__pycache__/
backend/src/celery_app/tasks/__pycache__/
backend/src/celery_app/__pycache__/
backend/src/core/__pycache__/
backend/tests/__pycache__/
```

### 前端建置檔案
```bash
# Nuxt.js 建置產物（開發時會自動重建）
frontend/.nuxt/
frontend/.nuxt/dist/

# 注意：node_modules 不建議刪除，除非要重新安裝
```

### 日誌檔案
```bash
# 應用程式日誌（可定期清理）
backend/logs/app.log
```

## ⚠️ 需要檢視確認的除錯檔案

### 根目錄除錯檔案
以下檔案位於專案根目錄，疑似為開發過程中的除錯檔案：

1. **debug_broker_format.py** (4,249 bytes)
   - 用途：除錯 broker 資料格式
   - 建議：如果 broker 爬蟲功能已穩定，可刪除

2. **debug_parser.py** (4,270 bytes)
   - 用途：除錯資料解析器
   - 建議：如果資料解析功能已穩定，可刪除

3. **simple_broker_test.py** (5,419 bytes)
   - 用途：簡單 broker 測試
   - 建議：如果有正式測試套件涵蓋，可刪除

4. **test_api.html** (3,131 bytes)
   - 用途：HTML API 測試頁面
   - 建議：現在有完整的前端 API 整合頁面，可刪除

5. **test_api_endpoints.py** (9,197 bytes)
   - 用途：API 端點測試腳本
   - 建議：如果功能已併入正式測試套件，可刪除

6. **test_broker_urls.py** (7,132 bytes)
   - 用途：測試 broker URL 連接
   - 建議：如果 broker 服務已穩定，可刪除

7. **test_crawl_endpoint.py** (3,340 bytes)
   - 用途：測試爬蟲端點
   - 建議：功能應已整合到正式 API，可刪除

8. **test_db_connection.py** (4,473 bytes)
   - 用途：測試資料庫連接
   - 建議：現在有健康檢查 API 涵蓋此功能，可刪除

9. **test_stock_filter.py** (5,304 bytes)
   - 用途：測試股票篩選功能
   - 建議：如果功能已整合到正式服務，可刪除

### 除錯用目錄
10. **test_daily_scraper/** 整個目錄
    - 內含：requirements.txt, src/, tests/, test_real_data.py
    - 用途：日線資料爬蟲測試環境
    - 建議：如果主專案的爬蟲功能已完成且穩定，此實驗性目錄可刪除

## 📋 保留的測試檔案（重要）

### 後端正式測試套件 (保留)
```bash
backend/tests/test_api_integration_complete.py    # ✅ 新建立的完整 API 測試
backend/tests/test_health.py                     # ✅ 健康檢查測試
backend/tests/test_moving_averages_api.py        # ✅ 均線 API 測試
backend/tests/test_stock_history_api.py          # ✅ 股票歷史 API 測試
backend/tests/test_stock_list_api.py             # ✅ 股票清單 API 測試
backend/tests/conftest.py                        # ✅ pytest 配置
```

### 前端正式測試套件 (保留)
```bash
frontend/tests/api-integration.test.js           # ✅ 新建立的前端 API 測試
frontend/tests/setup.js                          # ✅ 測試配置
frontend/vitest.config.js                        # ✅ Vitest 配置
```

## 🧹 建議的清理步驟

### 第一階段：安全清理
```bash
# 1. 清理 Python 編譯檔案
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# 2. 清理建置快取
rm -rf backend/.pytest_cache/
rm -rf frontend/.nuxt/

# 3. 清理日誌檔案（可選）
rm -f backend/logs/app.log
```

### 第二階段：檢視除錯檔案
請逐一檢視根目錄的除錯檔案，確認功能是否已整合到正式系統中：

1. 檢查 `debug_broker_format.py` 和 `debug_parser.py` 的功能是否已整合到 `DailyDataService`
2. 確認 `test_api_endpoints.py` 的測試案例是否已涵蓋在新的 `test_api_integration_complete.py` 中
3. 驗證 `test_db_connection.py` 的功能是否已由健康檢查 API 取代
4. 檢查 `test_daily_scraper/` 目錄是否為舊的實驗性代碼

### 第三階段：確認刪除
如果確認除錯檔案的功能已整合到正式系統，可執行：

```bash
# 刪除根目錄除錯檔案
rm debug_broker_format.py
rm debug_parser.py
rm simple_broker_test.py
rm test_api.html
rm test_api_endpoints.py
rm test_broker_urls.py
rm test_crawl_endpoint.py
rm test_db_connection.py
rm test_stock_filter.py

# 刪除實驗性目錄（請先確認不需要）
rm -rf test_daily_scraper/
```

## 📊 預估可釋放空間

- Python 編譯檔案：約 10-20 MB
- 前端建置檔案：約 50-100 MB
- 根目錄除錯檔案：約 50 KB
- 實驗性目錄：約 10 KB
- **總計預估**：約 60-120 MB

## ⚡ 執行建議

1. **先執行第一階段**的安全清理，這些檔案可以安全刪除且會自動重建
2. **仔細檢視第二階段**的除錯檔案，確認功能是否已整合
3. **備份重要的除錯邏輯**到正式代碼中（如有需要）
4. **最後執行第三階段**的刪除操作

## 🔄 後續維護

建議在 `.gitignore` 中加入以下規則以避免未來提交不必要檔案：

```bash
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Nuxt.js
.nuxt/
dist/

# Logs
*.log
logs/

# Debug files
debug_*.py
test_*.py  # 除非在 tests/ 目錄中
```