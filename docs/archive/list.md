# 台灣股票分析系統 - 功能清單

## 專案概覽

這是一個**台灣股票市場分析系統**，採用前後端分離架構，提供股票資料蒐集、技術分析、投信外資買賣超分析等完整功能。

### 技術架構

**後端 (Backend):**
- Python 3.11 + FastAPI
- SQLAlchemy ORM + PostgreSQL 資料庫
- Celery + Redis 背景任務處理
- pandas + numpy 技術分析計算
- Docker + Docker Compose 容器化部署

**前端 (Frontend):**
- Nuxt.js 3 + Vue.js
- Pinia 狀態管理
- Nuxt UI 介面框架
- Chart.js 圖表視覺化

---

## 完整功能清單

### 1. 健康檢查與監控 (Health Check)

**API 端點：** `/api/v1/health/*`

**功能說明：**
- 基礎健康檢查 (`/api/v1/health/`)
- 詳細系統健康狀態 (`/api/v1/health/detailed`)
- Kubernetes 準備度探針 (`/api/v1/health/readiness`)
- Kubernetes 存活度探針 (`/api/v1/health/liveness`)
- 系統狀態監控和服務可用性檢測

---

### 2. 股票清單管理 (Stock Management)

**API 端點：** `/api/v1/stocks/*`

**主要功能：**

#### 2.1 股票列表查詢
- **端點：** `GET /api/v1/stocks/list`
- **功能：** 從資料庫獲取股票列表，支援分頁、市場篩選（TSE/TPEx）、關鍵字搜尋
- **參數：** page, limit, market, search
- **回傳：** 股票代號、名稱、市場別、產業別、價格、漲跌幅等資訊

#### 2.2 可用股票代號
- **端點：** `GET /api/v1/stocks/symbols`
- **功能：** 獲取系統中所有可用的股票代號清單

#### 2.3 當前價格查詢
- **端點：** `GET /api/v1/stocks/{symbol}/current`
- **功能：** 查詢特定股票的即時價格資訊

#### 2.4 歷史資料查詢
- **端點：** `GET /api/v1/stocks/{symbol}/historical`
- **功能：** 查詢股票歷史價格資料（指定日期區間）

#### 2.5 資料更新觸發
- **端點：** `POST /api/v1/stocks/{symbol}/update` - 更新單一股票
- **端點：** `POST /api/v1/stocks/update-all` - 批次更新所有股票
- **功能：** 觸發背景任務更新市場資料

---

### 3. 股票清單同步 (Stock Synchronization)

**API 端點：** `/api/v1/sync/*`

**服務類別：** `StockListService`

**主要功能：**

#### 3.1 股票清單爬取與同步
- **端點：** `GET /api/v1/sync/stocks/crawl`
- **功能：**
  - 從證交所（TSE）和櫃買中心（TPEx）API 爬取最新股票清單
  - 自動過濾：僅保留 4 位數且非 0 開頭的股票代碼
  - 智能更新：新增新股票、更新現有股票資訊
  - 錯誤容錯：部分 API 失敗時仍可繼續處理
- **資料來源：**
  - TSE: `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL`
  - TPEx: `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes`

#### 3.2 股票統計資訊
- **端點：** `GET /api/v1/sync/stocks/count`
- **功能：** 獲取資料庫中的股票總數統計

#### 3.3 股票代號驗證
- **端點：** `GET /api/v1/sync/stocks/validate/{symbol}`
- **功能：** 驗證股票代號是否存在於系統中

#### 3.4 股票同步
- **端點：** `POST /api/v1/sync/stocks/sync`
- **功能：** 手動觸發股票清單同步作業

**已完成狀態：** 2025/01/09 完成，測試驗證成功（成功爬取 1,053 支 TSE 股票）

---

### 4. 股票歷史資料管理 (Stock History Data)

**API 端點：** `/api/v1/data/*`

**服務類別：** `DailyDataService`, `StockHistoryService`

**主要功能：**

#### 4.1 歷史日線資料爬取
- **端點：** `GET /api/v1/data/daily/{symbol}`
- **功能：**
  - 從 8 個券商網站同時爬取股票還原日線資料
  - 支援多資料源容錯機制（單一來源失敗不影響其他來源）
  - 智能資料解析：支援 tab 分隔、逗號分隔等多種格式
  - 完整資料驗證：價格邏輯驗證、成交量驗證
  - 自動去重：重複資料自動處理

**8 個券商資料來源：**
1. 富邦證券 (fubon-ebrokerdj.fbs.com.tw)
2. MoneyDJ (justdata.moneydj.com)
3. 元大證券 (jdata.yuanta.com.tw)
4. MegaDJ (moneydj.emega.com.tw)
5. 富邦投信 (djfubonholdingfund.fbs.com.tw)
6. 玉山證券 (sjmain.esunsec.com.tw)
7. 凱基證券 (kgieworld.moneydj.com)
8. 元富證券 (newjust.masterlink.com.tw)

#### 4.2 歷史資料查詢
- **端點：** `GET /api/v1/data/history/{symbol}`
- **功能：**
  - 查詢特定股票的歷史資料
  - 支援日期範圍篩選、分頁、排序
  - 回傳開高低收、成交量、均線等完整資料

#### 4.3 股票統計資訊
- **端點：** `GET /api/v1/data/history/{symbol}/stats`
- **功能：** 獲取股票的統計資訊（總筆數、日期範圍、價格統計等）

#### 4.4 最新交易日期
- **端點：** `GET /api/v1/data/history/{symbol}/latest-date`
- **功能：** 查詢股票最新的交易日期

**已完成狀態：** 2025/09/09 完成，包含完整 TDD 測試（17 項測試）

---

### 5. 移動平均線計算 (Moving Averages)

**API 端點：** `/api/v1/moving-averages/*`

**服務類別：** `MovingAveragesService`

**資料表：** `moving_averages`

**主要功能：**

#### 5.1 均線統計資訊
- **端點：** `GET /api/v1/moving-averages/statistics`
- **功能：**
  - 已計算均線的股票數量
  - 總均線記錄數量
  - 最新計算日期
  - 計算完整度百分比

#### 5.2 同步計算均線
- **端點：** `POST /api/v1/moving-averages/calculate`
- **功能：**
  - 同步計算指定股票的移動平均線
  - 支援自定義均線週期（預設：5, 10, 20, 60, 120, 240 日）
  - 強制重新計算選項
  - 適用於小量股票的即時計算

#### 5.3 查詢股票均線資料
- **端點：** `GET /api/v1/moving-averages/query/{stock_code}`
- **功能：**
  - 查詢特定股票的均線歷史資料
  - 支援日期範圍篩選
  - 支援指定均線週期查詢
  - 分頁查詢功能

#### 5.4 非同步計算均線
- **端點：** `POST /api/v1/moving-averages/calculate-async`
- **功能：**
  - 啟動背景任務批次計算均線
  - 支援批次處理以降低記憶體使用
  - 提供任務進度追蹤
  - 適用於大量股票計算

#### 5.5 任務狀態查詢
- **端點：** `GET /api/v1/moving-averages/task-status/{task_id}`
- **功能：** 查詢非同步任務執行狀態和進度

#### 5.6 取消非同步任務
- **端點：** `DELETE /api/v1/moving-averages/task/{task_id}`
- **功能：** 取消正在執行的非同步計算任務

#### 5.7 驗證均線資料一致性
- **端點：** `GET /api/v1/moving-averages/validate`
- **功能：**
  - 檢查均線資料的完整性和一致性
  - 自動修復異常的均線值
  - 補充缺失的資料

#### 5.8 清除均線資料
- **端點：** `POST /api/v1/moving-averages/clear`
- **功能：** 清除指定或全部股票的均線資料

**支援的均線週期：** MA5, MA10, MA20, MA60, MA120, MA240

**已完成狀態：** 已實作完整 API 端點和服務邏輯

---

### 6. 投信外資買賣超分析 (Institutional Trading)

**API 端點：** `/api/v1/institutional-trading/*`

**服務類別：** `InstitutionalTradingService`

**資料表：** `institutional_trading_data`

**主要功能：**

#### 6.1 統計資訊
- **端點：** `GET /api/v1/institutional-trading/statistics`
- **功能：**
  - 總記錄數、股票數、資料天數
  - 最早/最新日期
  - 最新一日統計摘要

#### 6.2 更新最新交易日資料
- **端點：** `POST /api/v1/institutional-trading/update/latest`
- **功能：**
  - 智能尋找最近有資料的交易日並更新
  - 自動回溯最近 7 天尋找可用資料

#### 6.3 批次更新資料
- **端點：** `POST /api/v1/institutional-trading/update/batch`
- **參數：** days_back（1-365天，預設30天）
- **功能：** 批次更新近期投信外資買賣超資料

#### 6.4 更新指定日期資料
- **端點：** `POST /api/v1/institutional-trading/update/{date}`
- **參數：** date (YYYYMMDD 格式)
- **功能：** 更新特定交易日的投信外資買賣超資料

#### 6.5 查詢股票買賣超資料
- **端點：** `GET /api/v1/institutional-trading/stock/{stock_code}`
- **參數：** limit（1-365，預設30）
- **功能：** 查詢特定股票的投信外資買賣超歷史資料

#### 6.6 資料完整性檢查
- **端點：** `GET /api/v1/institutional-trading/check/completeness`
- **功能：**
  - 分析資料完整性
  - 識別缺少資料的股票
  - 計算完整率百分比

#### 6.7 每日買賣超總覽
- **端點：** `GET /api/v1/institutional-trading/summary/{date}`
- **功能：** 獲取指定日期的買賣超總覽統計

#### 6.8 最新買賣超排名
- **端點：** `GET /api/v1/institutional-trading/rankings/latest`
- **參數：**
  - category: foreign（外資）, investment_trust（投信）, dealer（自營商）, total（三大法人）
  - limit: 1-100，預設20
  - sort_by: amount（按金額）, capital_ratio（按股本比）
- **功能：** 獲取最新交易日的買超/賣超排名

#### 6.9 股本比累積排名
- **端點：** `GET /api/v1/institutional-trading/capital-ratio/rankings`
- **參數：** days_back, limit
- **功能：** 指定期間的股本比累積排名分析

#### 6.10 股本比趨勢分析
- **端點：** `GET /api/v1/institutional-trading/capital-ratio/trends`
- **功能：** 每日股本比趨勢資料，支援圖表視覺化

#### 6.11 歷史買賣超排名
- **端點：** `GET /api/v1/institutional-trading/rankings/{date}`
- **功能：** 查詢指定日期的買賣超排名

**資料欄位包含：**
- 外陸資買賣超（不含外資自營商）
- 外資自營商買賣超
- 投信買賣超
- 自營商買賣超（含自行買賣、避險）
- 三大法人合計買賣超
- 股本比計算（買賣超/股本 × 100%）

---

### 7. 股本資料管理 (Capital Stock)

**API 端點：** `/api/v1/capital-stock/*`

**服務類別：** `CapitalStockService`

**主要功能：**

#### 7.1 股本統計資訊
- **端點：** `GET /api/v1/capital-stock/statistics`
- **功能：**
  - 總股票數、有股本資料的股票數
  - 完整率百分比
  - TSE/OTC 分類統計
  - 股本規模分布（大/中/小型股）

#### 7.2 更新所有股本資料
- **端點：** `POST /api/v1/capital-stock/update`
- **功能：**
  - 從政府開放資料平台爬取最新股本資料
  - 支援 TSE（上市）和 OTC（上櫃）公司
  - 自動更新現有股票、新增新股票

#### 7.3 查詢股票股本
- **端點：** `GET /api/v1/capital-stock/{stock_code}`
- **功能：** 查詢特定股票的股本資料（含股本分類）

#### 7.4 股本完整性檢查
- **端點：** `GET /api/v1/capital-stock/check/completeness`
- **功能：** 檢查哪些股票缺少股本資料

**已完成狀態：** Point 14 完成（2025/09/23）

---

### 8. 交易日分析 (Trading Days Analysis)

**API 端點：** `/api/v1/trading-days/*`

**服務類別：** `TradingDaysService`

**主要功能：**

#### 8.1 缺少交易日摘要
- **端點：** `GET /api/v1/trading-days/missing-summary`
- **參數：** days_back（1-365天，預設30天）
- **功能：**
  - 分析期間統計
  - 缺少的交易日列表
  - 資料完整性評分
  - 可能原因分析

#### 8.2 股票資料完整性分析
- **端點：** `GET /api/v1/trading-days/stock-completeness`
- **參數：** stock_code（選填）, days_back
- **功能：**
  - 分析特定股票或所有股票的資料完整性
  - 缺少資料的詳細分析
  - 資料完整率排名

---

### 9. 證交所官方 API (TWSE Official API)

**API 端點：** `/api/v1/twse/*`

**服務類別：** `TWSEDataService`

**主要功能：**
- 整合證交所官方 API
- 提供標準化的台股資料查詢介面
- 支援即時行情、歷史資料等查詢

---

### 10. 選股推薦 (Stock Selection)

**API 端點：** `/api/v1/stock-selection/*`

**服務類別：** `StockSelectionService`

**主要功能：**
- 基於技術指標的選股邏輯
- 多條件篩選功能
- 股票評分和排名
- 推薦股票清單生成

---

### 11. 任務執行與管理 (Task Execution)

**API 端點：** `/api/v1/tasks/*`, `/api/v1/task-execution/*`

**服務類別：** `TaskExecutionService`

**資料表：** `task_execution_logs`

**主要功能：**

#### 11.1 手動任務執行
- **類型：**
  - 優化股票爬蟲 (optimized_stock_crawl)
  - 循序股票爬蟲 (sequential_stock_crawl)
  - 一般資料更新 (data_update)
  - 技術分析 (analysis)

#### 11.2 任務執行記錄
- 任務名稱、類型、參數
- 執行狀態（running, completed, failed, cancelled）
- 開始/結束時間、執行時長
- 進度追蹤（0-100%）
- 處理數量統計（已處理、成功、錯誤）
- 結果摘要和錯誤訊息

#### 11.3 批次更新服務
**優化批次更新器 (OptimizedBatchUpdater):**
- 並行處理（可設定 worker 數量）
- 批次資料庫操作
- 智能跳過機制（避免重複爬取）
- 進度追蹤和日誌記錄

**循序批次更新器 (SequentialBatchUpdater):**
- 循序處理股票（避免 API rate limit）
- 批次提交資料庫
- 延遲控制（可設定股票間延遲）
- 適合大量股票的穩定更新

---

### 12. Celery 背景任務 (Celery Tasks)

**任務模組：** `src/celery_app/tasks/`

**主要任務：**

#### 12.1 資料蒐集任務 (data_collection.py)
- `update_market_data`: 更新市場資料
- `fetch_historical_data`: 爬取歷史資料
- 定時排程自動更新

#### 12.2 技術分析任務 (analysis.py)
- `run_technical_analysis`: 執行技術分析
- `generate_signals`: 生成交易信號
- 均線、RSI、MACD 等指標計算

**Celery 配置：**
- Broker: Redis
- Result Backend: Redis
- Task Serializer: JSON
- Timezone: Asia/Taipei
- 支援定時排程 (Celery Beat)
- 監控介面: Celery Flower

---

## 前端功能頁面

### 儀表板 (Dashboard)
- `/dashboard/overview` - 系統總覽
- `/dashboard/analytics` - 分析儀表板

### 股票管理 (Stocks)
- `/stocks/list` - 股票清單
- `/stocks/history` - 歷史資料查詢

### 市場資料 (Market Data)
- `/market-data/update` - 資料更新管理
- `/market-data/historical` - 歷史資料瀏覽
- `/market-data/moving-averages` - 均線管理
- `/market-data/quality` - 資料品質檢查
- `/market-data/stock-selection` - 選股功能
- `/market-data/institutional-trading` - 投信外資買賣超
- `/market-data/trading-rankings` - 買賣排名
- `/market-data/capital-stock` - 股本資料
- `/market-data/capital-ratio-analysis` - 股本比分析

### 選股篩選 (Screening)
- `/screening/recommendations` - 股票推薦

### 任務管理 (Tasks)
- `/tasks/manual` - 手動任務執行
- `/tasks/scheduled` - 排程任務管理

### API 整合 (API Integration)
- `/api-integration/index` - API 測試與整合

### 系統設定 (Settings)
- `/settings/index` - 一般設定
- `/settings/theme` - 主題設定
- `/settings/ui` - UI 設定
- `/settings/users` - 使用者管理

### 其他
- `/help/index` - 說明文件
- `/auth/login` - 登入
- `/auth/register` - 註冊

---

## 資料庫模型

### 核心資料表

1. **stocks** - 股票基本資訊
   - 股票代號、名稱、市場別、產業別
   - 實收資本額、股本更新時間
   - 啟用狀態

2. **stock_daily_data** - 股票日線資料
   - 交易日期、開高低收價格
   - 成交量、成交額
   - 價差、漲跌幅
   - 簡易均線（MA5, MA10, MA20）
   - 資料來源、品質標記

3. **moving_averages** - 移動平均線
   - 完整均線數據（MA5, MA10, MA20, MA60, MA120, MA240）
   - 交易日期索引
   - 股票代號關聯

4. **technical_indicators** - 技術指標
   - RSI、MACD、KD 指標
   - 交易日期索引

5. **stock_scores** - 股票評分
   - 型態評分、趨勢評分、成交量評分
   - 總評分、排名

6. **institutional_trading_data** - 投信外資買賣超
   - 外陸資、外資自營商買賣超
   - 投信、自營商買賣超
   - 三大法人合計買賣超

7. **task_execution_logs** - 任務執行記錄
   - 任務名稱、類型、參數
   - 執行狀態、進度
   - 處理統計、錯誤訊息

---

## 開發特色

### TDD 測試驅動開發
- 所有核心功能先撰寫測試再實作
- pytest + httpx 完整測試覆蓋
- 單元測試、整合測試、API 測試

### Docker 容器化部署
- PostgreSQL 容器（PORT: 9221）
- Redis 容器（PORT: 9321）
- Backend API（PORT: 9121）
- Celery Worker/Beat/Flower
- Frontend Nuxt.js（PORT: 3000）

### 程式碼品質管理
- Black 程式碼格式化
- isort import 排序
- flake8 程式碼檢查
- mypy 類型檢查
- pre-commit hooks

### API 文件自動生成
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI 規範

---

## 專案狀態

### 已完成功能 (Phase 1-2)
- ✅ 專案架構建立
- ✅ 資料庫設計完成
- ✅ 股票清單同步功能
- ✅ 歷史日線資料爬取
- ✅ 均線計算功能
- ✅ 投信外資買賣超分析
- ✅ 股本資料管理
- ✅ 交易日分析功能
- ✅ Docker 容器化部署
- ✅ Celery 背景任務框架

### 進行中功能
- 🔧 完整技術分析功能
- 🔧 選股推薦演算法優化
- 🔧 前端介面完善

### 計劃中功能
- 📋 進階技術指標（布林通道、威廉指標等）
- 📋 機器學習選股模型
- 📋 即時價格串流（WebSocket）
- 📋 進階告警系統

---

## 總結

這個專案是一個**功能完整的台灣股票分析系統**，涵蓋從資料蒐集、技術分析到投資決策支援的完整流程，採用現代化的技術架構和開發流程，適合投資分析和量化交易應用。

### 核心優勢
1. **完整的資料蒐集流程** - 從多個券商來源爬取股票資料，確保資料完整性
2. **強大的技術分析功能** - 均線、投信外資買賣超、股本分析等多維度分析
3. **現代化架構** - FastAPI + Nuxt.js，前後端分離，容易擴展
4. **高品質程式碼** - TDD 測試驅動開發，完整的測試覆蓋
5. **容器化部署** - Docker Compose 一鍵部署，便於開發和維護

---

*最後更新日期：2025-10-30*
