# 股票分析系統專案任務清單

## 專案概述
股票分析系統，提供每日股票資料更新、技術指標計算及線型分析功能。

**技術架構：**
- 前端：Nuxt.js 3 + Pinia + Nuxt UI（現有admin專案）
- 後端：Python + FastAPI + SQLAlchemy + PostgreSQL
- 任務調度：Celery + Redis
- 技術分析：pandas + TA-Lib + numpy
- 部署：Docker + Docker Compose
- 測試：pytest + httpx（TDD開發模式）

---

## 1. 專案結構和初始設定任務

### 1.1 專案架構建立
**優先級：** P0（必須）  
**預估時間：** 2天  
**依賴關係：** 無  
**負責模組：** 基礎建設

**任務內容：** ✅ **已完成**
- [x] 建立專案根目錄結構
- [x] 設定 backend/ 目錄架構
- [x] 配置 Python 虛擬環境
- [x] 建立 requirements.txt 和 pyproject.toml
- [x] 建立 .env.example 環境變數範本
- [x] 設定 Black + isort + flake8 程式碼規範
- [x] 建立 .gitignore 檔案

**專案結構：**
```
stock-analysis-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── celery_app/
│   │   ├── __init__.py
│   │   ├── worker.py
│   │   └── tasks/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/（現有admin專案）
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

### 1.2 環境配置設定
**優先級：** P0（必須）  
**預估時間：** 1天  
**依賴關係：** 1.1  
**負責模組：** 基礎建設

**任務內容：** ✅ **已完成**
- [x] 建立 .env 環境變數管理
- [x] 設定 PORT 統一管理機制
- [x] 配置開發/測試/生產環境區分
- [x] 建立 Docker 環境配置

### 1.3 Docker 容器化設定
**優先級：** P1（重要）  
**預估時間：** 1天  
**依賴關係：** 1.1, 1.2  
**負責模組：** 基礎建設

**任務內容：** ✅ **已完成**
- [x] 建立 Dockerfile（Python FastAPI 後端）
- [x] 建立 docker-compose.yml（不使用version欄位）
- [x] 設定 PostgreSQL 容器
- [x] 設定 Redis 容器（用於 Celery）
- [x] 設定 Celery Worker 容器
- [x] 配置容器間網路通訊
- [x] 設定 .env 變數的 PORT 管理

---

## 2. 資料庫設計和設定任務

### 2.1 資料庫架構設計
**優先級：** P0（必須）  
**預估時間：** 2天  
**依賴關係：** 1.2  
**負責模組：** 資料層

**任務內容：** ✅ **已完成**
- [x] 設計股票基本資訊表（stocks）
- [x] 設計股票日線資料表（stock_daily_data）
- [x] 設計技術指標表（technical_indicators）、均線表、評分表
- [x] 設計系統配置表（system_configs）
- [x] 建立 ER 圖文件

**資料表結構：**
```sql
-- 股票基本資訊
stocks (
  id, symbol, name, market, industry, 
  is_active, created_at, updated_at
)

-- 股票日線資料
stock_daily_data (
  id, stock_id, date, open_price, high_price, 
  low_price, close_price, volume, adjusted_close,
  created_at, updated_at
)

-- 技術指標
technical_indicators (
  id, stock_id, date, ma5, ma10, ma20, ma60,
  created_at, updated_at
)
```

### 2.2 資料庫遷移設定
**優先級：** P0（必須）  
**預估時間：** 1天  
**依賴關係：** 2.1  
**負責模組：** 資料層

**任務內容：** ✅ **已完成**
- [x] 設定 Alembic migration 工具
- [x] 建立初始化遷移檔案
- [x] 建立種子資料（seed data）
- [x] 設定資料庫索引優化

### 2.3 SQLAlchemy 模型建立
**優先級：** P0（必須）  
**預估時間：** 2天  
**依賴關係：** 2.1, 2.2  
**負責模組：** 資料層

**任務內容：** ✅ **已完成**
- [x] 建立 Stock 模型 (SQLAlchemy)
- [x] 建立 StockDailyData 模型 (SQLAlchemy)
- [x] 建立 TechnicalIndicator、MovingAverages、StockScores 模型
- [x] 設定模型關聯關係
- [x] 建立 Pydantic 資料驗證 schema

---

## 3. 後端API開發任務

### 3.1 核心基礎架構
**優先級：** P0（必須）  
**預估時間：** 2天  
**依賴關係：** 1.1, 1.2, 2.3  
**負責模組：** API核心

**任務內容：** ✅ **已完成**
- [x] 設定 FastAPI 應用程式
- [x] 建立全域例外處理器
- [x] 設定 API 路由架構 (APIRouter)
- [x] 建立統一回應格式 (BaseResponse schema)
- [x] 設定 CORS 中介軟體
- [x] 建立健康檢查端點 (/health)
- [x] 設定自動 API 文件生成 (OpenAPI)

### 3.2 股票資料管理模組
**優先級：** P0（必須）  
**預估時間：** 3天  
**依賴關係：** 3.1  
**負責模組：** 股票資料

**API端點：**
- [ ] `GET /api/stocks` - 取得股票列表
- [ ] `POST /api/stocks` - 新增股票
- [ ] `PUT /api/stocks/:id` - 更新股票資訊
- [ ] `DELETE /api/stocks/:id` - 刪除股票
- [ ] `GET /api/stocks/:id/daily-data` - 取得股票日線資料

**服務層功能：**
- [ ] 股票列表 CRUD 操作
- [ ] 股票資料驗證邏輯
- [ ] 重複股票檢查機制

### 3.3 資料擷取模組
**優先級：** P0（必須）  
**預估時間：** 4天  
**依賴關係：** 3.2  
**負責模組：** 資料擷取

**任務內容：**
- [x] 建立外部API串接服務 (使用 httpx) ✅ **完成 - 2025/01/09**
- [x] 實作股票清單自動更新功能 ✅ **完成 - 2025/01/09**
- [ ] 實作股票日線資料擷取功能 (還原日線)
- [ ] 建立資料還原處理邏輯 (pandas 處理)
- [ ] 實作增量更新機制
- [ ] 建立資料品質檢查機制
- [ ] 設定 Celery 排程任務框架

**API端點：**
- [x] `POST /api/v1/sync/stocks/sync` - 同步股票清單 ✅ **完成 - 2025/01/09**
- [x] `GET /api/v1/sync/stocks/count` - 取得股票統計 ✅ **完成 - 2025/01/09**  
- [x] `GET /api/v1/sync/stocks/validate/{symbol}` - 驗證股票代號 ✅ **完成 - 2025/01/09**
- [x] `GET /api/v1/sync/stocks/crawl` - 爬取股票列表並更新資料庫 ✅ **完成 - 2025/09/09**
- [ ] `POST /api/data/update-daily/:stockId` - 更新單一股票日線
- [ ] `POST /api/data/update-all-daily` - 更新所有股票日線
- [ ] `GET /api/data/sync-status` - 取得同步狀態

**已完成功能詳情：**
✅ **股票列表擷取功能 (2025/01/09)：**
- TSE/TPEx股票API串接 (使用httpx)
- 股票過濾邏輯：僅保留4位數非0開頭股票代碼 
- StockListService完整實作 (fetch_tse_stocks, fetch_tpex_stocks, filter_valid_stocks)
- 資料驗證和儲存機制 (validate_stock_data, save_stocks_to_database)
- 完整TDD測試覆蓋 (unittest + integration + API tests)
- API端點實作和測試驗證通過

✅ **GET股票爬取API端點 (2025/09/09)：**
- 新增 `GET /api/v1/sync/stocks/crawl` 端點
- 實作即時爬取和資料庫更新功能
- 優雅處理部分API失敗 (partial_success狀態)
- 回傳詳細統計資訊：總股票數、各市場股票數、新增/更新統計
- 完整TDD測試覆蓋：成功場景、部分失敗、完全失敗、冪等性測試
- 實際測試驗證：成功爬取1,053支TSE股票並儲存至資料庫
- 錯誤處理：TPEx API安全重新導向處理

### 3.4 技術指標計算模組
**優先級：** P0（必須）  
**預估時間：** 3天  
**依賴關係：** 3.3  
**負責模組：** 技術分析

**任務內容：**
- [ ] 建立均線計算服務（MA5, MA10, MA20, MA60）使用 pandas + TA-Lib
- [ ] 實作技術指標批次計算 (向量化計算)
- [ ] 建立指標資料儲存邏輯
- [ ] 實作歷史指標重算功能
- [ ] 整合 numpy 進行數值運算最佳化

**API端點：**
- [ ] `POST /api/indicators/calculate/:stockId` - 計算單一股票指標
- [ ] `POST /api/indicators/calculate-all` - 計算所有股票指標
- [ ] `GET /api/indicators/:stockId` - 取得股票技術指標

### 3.5 線型分析模組
**優先級：** P1（重要）  
**預估時間：** 4天  
**依賴關係：** 3.4  
**負責模組：** 線型分析

**任務內容：**
- [ ] 建立線型漂亮度評分演算法 (使用 pandas 向量化運算)
- [ ] 實作多頭排列判斷邏輯
- [ ] 建立黃金交叉/死亡交叉偵測
- [ ] 實作趨勢強度分析 (使用 numpy 統計函數)
- [ ] 建立股票推薦排序機制

**API端點：**
- [ ] `GET /api/analysis/beautiful-stocks` - 取得線型漂亮股票
- [ ] `GET /api/analysis/stock-score/:stockId` - 取得股票評分
- [ ] `GET /api/analysis/trends` - 取得市場趨勢分析

### 3.6 Celery 排程任務模組
**優先級：** P1（重要）  
**預估時間：** 2天  
**依賴關係：** 3.3, 3.4  
**負責模組：** 排程服務

**任務內容：**
- [ ] 設定 Celery + Redis 基礎架構
- [ ] 建立每日股票清單更新排程 (Celery Beat)
- [ ] 建立每日股價資料更新排程 (Celery Beat)
- [ ] 建立技術指標計算排程 (Celery Beat)
- [ ] 設定排程監控和錯誤處理 (Celery Flower)
- [ ] 建立排程狀態查詢API

---

## 4. 前端介面開發任務

### 4.1 核心佈局調整
**優先級：** P1（重要）  
**預估時間：** 2天  
**依賴關係：** 無  
**負責模組：** 前端核心

**任務內容：**
- [ ] 調整現有 admin 模板為股票分析介面
- [ ] 更新導航選單結構
- [ ] 建立股票分析專用佈局
- [ ] 設定 API 基礎配置

### 4.2 股票清單管理頁面
**優先級：** P1（重要）  
**預估時間：** 3天  
**依賴關係：** 4.1, 3.2  
**負責模組：** 股票管理

**功能頁面：**
- [ ] 股票清單顯示頁面（表格格式）
- [ ] 股票搜尋和篩選功能
- [ ] 股票新增/編輯/刪除功能
- [ ] 股票狀態管理介面
- [ ] 批次操作功能

### 4.3 股票資料展示頁面
**優先級：** P1（重要）  
**預估時間：** 4天  
**依賴關係：** 4.2, 3.3  
**負責模組：** 資料展示

**功能頁面：**
- [ ] 股票詳細資訊頁面
- [ ] 股價走勢圖表（使用 Chart.js 或 ECharts）
- [ ] 技術指標圖表顯示
- [ ] 歷史資料表格檢視
- [ ] 資料更新狀態顯示

### 4.4 線型分析儀表板
**優先級：** P1（重要）  
**預估時間：** 4天  
**依賴關係：** 4.3, 3.5  
**負責模組：** 分析儀表板

**功能頁面：**
- [ ] 線型漂亮股票排行榜
- [ ] 技術指標統計圖表
- [ ] 市場趨勢總覽
- [ ] 股票評分視覺化
- [ ] 自定義篩選條件介面

### 4.5 系統監控頁面
**優先級：** P2（一般）  
**預估時間：** 2天  
**依賴關係：** 4.1, 3.6  
**負責模組：** 系統監控

**功能頁面：**
- [ ] 資料同步狀態監控
- [ ] 排程任務執行狀況
- [ ] 系統健康狀態檢查
- [ ] 錯誤日誌檢視

---

## 5. 測試開發任務

### 5.1 後端單元測試 (pytest)
**優先級：** P0（必須）  
**預估時間：** 5天  
**依賴關係：** 對應後端功能模組  
**負責模組：** 測試

**測試覆蓋範圍：**
- [ ] 股票資料管理服務測試 (pytest + pytest-asyncio)
- [ ] 資料擷取服務測試 (pytest + httpx mock)
- [ ] 技術指標計算測試 (pytest + pandas testing)
- [ ] 線型分析演算法測試 (pytest + numpy testing)
- [ ] FastAPI 端點測試 (pytest + httpx TestClient)
- [ ] Celery 任務測試 (pytest + celery test utilities)
- [ ] 錯誤處理測試

### 5.2 整合測試
**優先級：** P1（重要）  
**預估時間：** 3天  
**依賴關係：** 5.1  
**負責模組：** 測試

**測試內容：**
- [ ] PostgreSQL + SQLAlchemy 整合測試
- [ ] 外部股票API整合測試
- [ ] Celery + Redis 排程任務整合測試
- [ ] FastAPI + Database 完整資料流程測試

### 5.3 前端測試
**優先級：** P2（一般）  
**預估時間：** 3天  
**依賴關係：** 前端功能完成  
**負責模組：** 測試

**測試內容：**
- [ ] 元件單元測試
- [ ] API串接測試
- [ ] 使用者介面測試
- [ ] 響應式設計測試

### 5.4 效能測試
**優先級：** P2（一般）  
**預估時間：** 2天  
**依賴關係：** 5.2  
**負責模組：** 測試

**測試內容：**
- [ ] API響應時間測試
- [ ] 大量資料處理效能測試
- [ ] 並發存取測試
- [ ] 資料庫查詢優化驗證

---

## 6. 部署和維運任務

### 6.1 CI/CD 流程建立
**優先級：** P1（重要）  
**預估時間：** 2天  
**依賴關係：** 1.3, 5.1  
**負責模組：** DevOps

**任務內容：**
- [ ] 設定 GitHub Actions 或類似CI工具
- [ ] 建立自動化測試流程
- [ ] 設定自動化部署流程
- [ ] 建立版本發佈機制

### 6.2 生產環境部署
**優先級：** P1（重要）  
**預估時間：** 2天  
**依賴關係：** 6.1  
**負責模組：** DevOps

**任務內容：**
- [ ] 設定生產環境 Docker 配置 (Python + FastAPI)
- [ ] 配置 Gunicorn + Uvicorn 生產部署
- [ ] 建立 PostgreSQL 資料庫備份機制
- [ ] 設定 SSL 憑證
- [ ] 配置 Nginx 反向代理（如需要）

### 6.3 監控和日誌系統
**優先級：** P2（一般）  
**預估時間：** 2天  
**依賴關係：** 6.2  
**負責模組：** 監控

**任務內容：**
- [ ] 建立應用程式日誌記錄
- [ ] 設定錯誤監控和告警
- [ ] 建立系統效能監控
- [ ] 設定資料庫監控

---

## 7. 專案里程碑

### Phase 1: 基礎建設 (第1-2週) ✅ 已完成
- ✅ 專案架構建立 (任務1.1-1.3 完成)
- ✅ 資料庫設計完成 (任務2.1-2.2 完成)
- ✅ 基礎API框架完成 (任務3.1 完成)

**完成項目詳細狀態：**
- ✅ 1.1 專案架構建立：Python + FastAPI 完整專案結構
- ✅ 1.2 環境配置設定：.env統一管理，PORT配置最佳化  
- ✅ 1.3 Docker容器化設定：docker-compose.yml完成（無version，環境變數管理）
- ✅ 2.1 資料庫架構設計：完整台股資料庫表結構設計
- ✅ 2.2 資料庫遷移設定：Alembic初始遷移檔案建立
- ✅ 2.3 SQLAlchemy模型建立：Stock、StockDailyData、均線、技術指標等模型完成
- ✅ 3.1 核心基礎架構：FastAPI應用、API端點、Celery任務框架

**✅ Docker測試驗證完成：**
- PostgreSQL容器成功啟動 (PORT: 9221)
- Redis容器成功啟動 (PORT: 9321)  
- 健康檢查通過，ready to accept connections
- 環境變數PORT管理正確運作

### Phase 2: 核心功能開發 (第3-5週)
- 股票資料管理完成
- 資料擷取功能完成
- 技術指標計算完成

### Phase 3: 分析功能開發 (第6-7週)
- 線型分析功能完成
- 前端介面完成
- 基礎測試完成

### Phase 4: 測試和優化 (第8-9週)
- 完整測試覆蓋
- 效能優化
- 部署準備

### Phase 5: 部署和維運 (第10週)
- 生產環境部署
- 監控系統建立
- 專案交付

---

## 8. 風險評估和備案

### 高風險項目：
1. **外部股票API穩定性** - 備案：準備多個資料來源
2. **大量資料處理效能** - 備案：資料分片處理，快取策略
3. **線型分析演算法複雜度** - 備案：階段性交付，逐步優化

### 技術債務管理：
- 定期code review
- 重構排程規劃
- 效能監控機制

---

## 9. 專案總預估

**總開發時間：** 10週（50個工作日）  
**主要開發人力：** 2-3人  
**測試覆蓋率目標：** 80%以上  
**效能目標：** API響應時間 < 500ms

---

## 備註

1. **TDD開發模式：** 所有核心功能必須先寫 pytest 測試再實作
2. **移除緩存功能：** 不實作緩存機制，直接查詢 PostgreSQL 資料庫
3. **環境變數管理：** 所有配置透過.env統一管理，PORT使用.env管理
4. **程式碼品質：** 遵循 Black + isort + flake8 規範，定期進行code review
5. **技術棧核心：** Python + FastAPI + SQLAlchemy + PostgreSQL + Celery + Redis
6. **數據分析：** 使用 pandas + TA-Lib + numpy 進行技術分析計算

**任務狀態說明：**
- P0：必須完成（影響核心功能）
- P1：重要（影響使用體驗）
- P2：一般（可延後實作）

## 10. 緊急修復和改進項目

### 10.1 Host Header 錯誤修復 ✅ **已完成 - 2025/09/09**
**問題描述：** 存取 `http://localhost:9121/api/v1/sync/stocks/count` 時出現 "Invalid host header" 錯誤

**修復內容：**
- [x] 修正 FastAPI TrustedHostMiddleware 配置
- [x] 允許 localhost, 127.0.0.1, 以及 debug 模式下所有主機 
- [x] 更新 DEBUG 模式設定預設值為 True
- [x] 移除 Docker 中的 TA-Lib 編譯問題（註解 TA-Lib 相關安裝）

### 10.2 API 測試項目建立 ✅ **已完成 - 2025/09/09**
**任務內容：**
- [x] 建立完整的 API 端點測試腳本 (`test_api_endpoints.py`)
- [x] 涵蓋所有主要端點測試（健康檢查、股票同步、驗證等）
- [x] Host Header 驗證測試
- [x] CORS 設定測試
- [x] 錯誤處理測試

**測試覆蓋範圍：**
- Root 端點: `/`
- Health 端點: `/api/v1/health` 
- Stock count 端點: `/api/v1/sync/stocks/count`
- Stock validation 端點: `/api/v1/sync/stocks/validate/{symbol}`
- API 文件端點: `/docs`, `/redoc`

### 10.3 Docker 和套件優化 ✅ **已完成 - 2025/09/09**
**優化內容：**
- [x] 移除 TA-Lib 從 Docker 建置流程（解決編譯問題）
- [x] 保留 requirements.txt 中註解說明原因
- [x] 修正 Celery Flower 套件缺失問題
- [x] 所有 Docker 服務正常運行（PostgreSQL, Redis, Backend, Celery Worker/Beat/Flower）

**✅ 服務驗證狀態：**
- stock_backend (API 服務): PORT 9121 ✅ 正常運行
- stock_postgres (資料庫): PORT 9221 ✅ 正常運行  
- stock_redis (快取): PORT 9321 ✅ 正常運行
- stock_celery_worker ✅ 正常運行
- stock_celery_beat ✅ 正常運行
- stock_celery_flower: PORT 9421 ✅ 正常運行

---

**更新記錄：**
- 2024-09-09：初版建立
- 2025-01-09：修正後端技術棧為 Python + FastAPI，整合 Celery + pandas + TA-Lib
- 2025-09-09：完成 Host Header 錯誤修復及 API 測試項目建立