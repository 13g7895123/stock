# 專案資料夾結構說明 (Project Structure)

> 更新時間: 2026-01-11  
> 版本: 1.0

## 📋 目錄概覽

```
stock/
├── backend/                    # Python FastAPI 後端服務
├── crawler-service/           # Go 高效能爬蟲服務
├── frontend/                   # Nuxt.js 前端應用
├── scripts/                   # 運維與開發腳本
├── docs/                      # 專案文件
├── data/                      # 資料儲存 (Docker volumes)
├── logs/                      # 應用程式日誌
├── uploads/                   # 檔案上傳暫存
├── docker-compose.yml         # Docker 服務編排
└── README.md                  # 專案說明
```

---

## 🐍 Backend (Python FastAPI)

**路徑**: `/backend/`  
**技術棧**: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery

### 目錄結構

```
backend/
├── src/                       # 原始碼根目錄
│   ├── main.py               # FastAPI 應用程式進入點
│   │
│   ├── api/                  # RESTful API 端點
│   │   ├── __init__.py
│   │   ├── health.py         # 健康檢查端點
│   │   ├── stocks.py         # 股票資料 API
│   │   ├── moving_averages.py # 均線資料 API
│   │   └── stock_history.py  # 歷史資料查詢 API
│   │
│   ├── core/                 # 核心配置模組
│   │   ├── config.py         # 應用程式配置 (環境變數、設定)
│   │   ├── database.py       # 資料庫連線設定
│   │   └── dependencies.py   # FastAPI 依賴注入
│   │
│   ├── models/               # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── stock.py          # 股票主檔模型
│   │   ├── stock_daily_data.py # 日線資料模型
│   │   └── moving_average.py # 均線資料模型
│   │
│   ├── schemas/              # Pydantic 資料驗證
│   │   ├── __init__.py
│   │   ├── stock.py          # 股票資料 Schema
│   │   ├── moving_average.py # 均線 Schema
│   │   └── response.py       # 統一回應格式
│   │
│   ├── services/             # 業務邏輯層
│   │   ├── __init__.py
│   │   ├── stock_service.py  # 股票資料服務
│   │   ├── moving_average_service.py # 均線計算服務
│   │   └── analysis_service.py # 技術分析服務
│   │
│   ├── utils/                # 工具函數
│   │   ├── __init__.py
│   │   ├── logger.py         # 日誌工具
│   │   ├── cache.py          # Redis 快取工具
│   │   └── helpers.py        # 通用輔助函數
│   │
│   └── celery_app/           # Celery 背景任務
│       ├── __init__.py
│       ├── tasks.py          # 任務定義 (均線更新、資料同步)
│       └── config.py         # Celery 配置
│
├── tests/                    # 測試套件
│   ├── conftest.py           # Pytest 配置與 Fixtures
│   ├── conftest_integration.py # 整合測試配置
│   ├── test_health.py        # 健康檢查測試
│   ├── test_stock_list_api.py # 股票列表 API 測試
│   ├── test_moving_averages_api.py # 均線 API 測試
│   ├── test_stock_history_api.py # 歷史資料 API 測試
│   ├── test_e2e_api.py       # 端到端測試
│   └── README_INTEGRATION_TESTS.md # 測試說明文件
│
├── alembic/                  # 資料庫遷移管理
│   ├── versions/             # 遷移腳本版本
│   ├── env.py                # Alembic 環境設定
│   └── script.py.mako        # 遷移腳本模板
│
├── sql/                      # SQL 腳本
│   └── init.sql              # 資料庫初始化腳本
│
├── logs/                     # 日誌檔案 (Docker volume)
├── uploads/                  # 上傳檔案暫存
│
├── alembic.ini               # Alembic 配置檔
├── pyproject.toml            # Python 專案配置 (Poetry)
├── requirements.txt          # Python 依賴清單
├── Dockerfile                # Docker 映像檔建構
├── Makefile                  # 常用指令封裝
├── pytest_integration.ini    # Pytest 整合測試配置
└── API_DOCUMENTATION.md      # API 文件
```

### 關鍵檔案說明

| 檔案 | 用途 |
|------|------|
| `src/main.py` | FastAPI 應用程式進入點，定義路由、中介軟體、CORS 設定 |
| `src/core/config.py` | 環境變數管理，應用程式全域配置 |
| `src/core/database.py` | 資料庫引擎、SessionLocal、Base 定義 |
| `alembic.ini` | Alembic 遷移工具配置，資料庫連線字串 |
| `pyproject.toml` | Poetry 專案定義，依賴版本鎖定 |
| `Makefile` | 常用指令封裝 (migrate, test, lint) |

### 重要端點

- `GET /health` - 健康檢查
- `GET /api/stocks` - 股票列表查詢
- `POST /api/stocks/batch-update` - 批次更新股票資料
- `GET /api/stocks/{stock_code}/history` - 股票歷史資料
- `GET /api/moving-averages` - 均線資料查詢
- `POST /api/moving-averages/update` - 更新均線資料

---

## 🔍 Crawler Service (Go)

**路徑**: `/crawler-service/`  
**技術棧**: Go 1.21+, PostgreSQL, Docker, Prometheus

### 目錄結構

```
crawler-service/
├── cmd/                      # 程式進入點
│   └── crawler/
│       └── main.go           # 主程式
│
├── internal/                 # 內部模組 (不可外部引用)
│   ├── api/                  # HTTP API 處理器
│   │   ├── handler.go        # 路由註冊
│   │   ├── health.go         # 健康檢查
│   │   ├── stock.go          # 股票 API
│   │   └── batch.go          # 批次更新 API
│   │
│   ├── config/               # 配置管理
│   │   ├── config.go         # 配置結構與載入
│   │   └── env.go            # 環境變數解析
│   │
│   ├── scraper/              # 爬蟲核心
│   │   ├── scraper.go        # 爬蟲介面定義
│   │   ├── fubon.go          # 富邦證券爬蟲實作
│   │   └── parser.go         # 資料解析器 (CSV 格式處理)
│   │
│   ├── storage/              # 資料儲存層
│   │   ├── postgres.go       # PostgreSQL 連線
│   │   ├── repository.go     # 資料庫操作介面
│   │   ├── batch.go          # 批次插入優化
│   │   └── models.go         # 資料模型定義
│   │
│   ├── service/              # 業務邏輯層
│   │   ├── stock_service.go  # 股票服務 (協調 scraper + storage)
│   │   └── batch_service.go  # 批次處理服務
│   │
│   ├── worker/               # 背景工作器
│   │   ├── worker.go         # 工作器介面
│   │   └── pool.go           # 工作池管理
│   │
│   └── metrics/              # 監控指標
│       └── prometheus.go     # Prometheus metrics 定義
│
├── pkg/                      # 公開套件 (可外部引用)
│   ├── logger/               # 日誌套件
│   │   └── logger.go
│   ├── httputil/             # HTTP 工具
│   │   └── client.go
│   └── errors/               # 錯誤處理
│       └── errors.go
│
├── configs/                  # 配置檔案
│   └── config.yaml           # 應用程式配置
│
├── deployments/              # 部署相關檔案
│   ├── Dockerfile            # 多階段建構映像檔
│   ├── docker-compose.yml    # 本地開發環境
│   ├── init-db.sql           # 資料庫初始化
│   ├── prometheus.yml        # Prometheus 配置
│   └── grafana/              # Grafana 儀表板
│
├── web/                      # 靜態網頁 (監控儀表板)
│   └── index.html
│
├── scripts/                  # 腳本工具
│   ├── build.sh              # 建構腳本
│   ├── deploy.sh             # 部署腳本
│   ├── install.sh            # 安裝腳本
│   └── start.sh              # 啟動腳本
│
├── tests/                    # 測試檔案
│   └── *_test.go
│
├── bin/                      # 編譯產出 (gitignore)
│   └── crawler
│
├── go.mod                    # Go 模組定義
├── go.sum                    # Go 依賴校驗
├── Makefile                  # 常用指令封裝
└── README.md                 # 服務說明
```

### 關鍵檔案說明

| 檔案 | 用途 |
|------|------|
| `cmd/crawler/main.go` | 程式進入點，初始化服務、啟動 HTTP server |
| `internal/scraper/parser.go` | **核心解析邏輯**，處理富邦證券 API 回應格式 |
| `internal/service/stock_service.go` | **業務邏輯層**，協調爬蟲與儲存，包含指標轉換邏輯 |
| `internal/storage/batch.go` | 批次插入優化，使用 `COPY` 或 `INSERT ... ON CONFLICT` |
| `deployments/Dockerfile` | 多階段建構 (golang:1.21-alpine → alpine:latest) |
| `configs/config.yaml` | 服務配置 (DB 連線、API 設定、工作池大小) |

### 重要端點

- `GET /health` - 健康檢查
- `GET /api/v1/stocks` - 股票列表
- `GET /api/v1/stocks/:code` - 單一股票資料
- `POST /api/v1/stocks/batch-update` - 批次更新股票歷史資料
- `GET /metrics` - Prometheus metrics

### 最近修復 (2026-01-11)

**問題**: 股票 2330 所有資料重複 (所有記錄顯示相同價格)  
**根本原因**: Go range loop 指標別名問題 (`&record.OpenPrice` 指向重複使用的迴圈變數)  
**解決方案**: 在 `stock_service.go` 中建立本地副本 `rec := record` 後再取址

```go
// 修復前 (錯誤)
for i, record := range validRecords {
    dbRecords[i] = storage.StockDailyData{
        OpenPrice: &record.OpenPrice, // ❌ 所有指標指向同一記憶體
        ...
    }
}

// 修復後 (正確)
for i, record := range validRecords {
    rec := record // ✅ 建立本地副本
    dbRecords[i] = storage.StockDailyData{
        OpenPrice: &rec.OpenPrice, // ✅ 每個指標指向獨立資料
        ...
    }
}
```

---

## 🎨 Frontend (Nuxt.js)

**路徑**: `/frontend/`  
**技術棧**: Nuxt 3, Vue 3, TypeScript, TailwindCSS, Pinia

### 目錄結構

```
frontend/
├── pages/                    # 頁面路由元件 (檔案系統路由)
│   ├── index.vue             # 首頁
│   ├── stocks/
│   │   ├── index.vue         # 股票列表
│   │   └── [code].vue        # 股票詳情 (動態路由)
│   └── analysis/
│       └── index.vue         # 技術分析頁面
│
├── components/               # 共用元件
│   ├── StockTable.vue        # 股票列表表格
│   ├── StockChart.vue        # 股票圖表
│   ├── MovingAverageChart.vue # 均線圖表
│   └── IndicatorPanel.vue    # 技術指標面板
│
├── composables/              # 組合式函數 (Composition API)
│   ├── useStockData.ts       # 股票資料邏輯
│   ├── useMovingAverage.ts   # 均線計算邏輯
│   └── useAuth.ts            # 身份驗證邏輯
│
├── stores/                   # Pinia 狀態管理
│   ├── stock.ts              # 股票狀態
│   ├── user.ts               # 使用者狀態
│   └── ui.ts                 # UI 狀態 (載入中、錯誤訊息)
│
├── layouts/                  # 版面配置
│   ├── default.vue           # 預設版面
│   └── admin.vue             # 管理後台版面
│
├── middleware/               # 路由中介軟體
│   └── auth.ts               # 身份驗證中介軟體
│
├── plugins/                  # Nuxt 插件
│   ├── api.ts                # API 客戶端
│   └── i18n.ts               # 國際化
│
├── assets/                   # 靜態資源
│   ├── css/
│   │   └── main.css          # 全域樣式
│   └── images/
│
├── locales/                  # 國際化翻譯檔
│   ├── zh-TW.json
│   └── en.json
│
├── tests/                    # 測試檔案
│   ├── unit/
│   └── e2e/
│
├── nuxt.config.ts            # Nuxt 配置
├── tailwind.config.js        # TailwindCSS 配置
├── tsconfig.json             # TypeScript 配置
├── package.json              # 依賴管理
├── Dockerfile                # Docker 映像檔
└── vitest.config.js          # Vitest 測試配置
```

### 關鍵檔案說明

| 檔案 | 用途 |
|------|------|
| `nuxt.config.ts` | Nuxt 應用程式配置，定義模組、插件、環境變數 |
| `app.vue` | 根元件，定義全域版面結構 |
| `tailwind.config.js` | TailwindCSS 主題與工具類別配置 |
| `composables/useStockData.ts` | 封裝股票資料獲取與狀態管理邏輯 |
| `stores/stock.ts` | Pinia store，全域股票狀態管理 |

---

## 🛠️ Scripts (運維腳本)

**路徑**: `/scripts/`  
**用途**: 開發、維運、部署自動化腳本

### 目錄結構

```
scripts/
├── maintenance/              # 維運腳本
│   ├── update_moving_averages.sh # 更新均線資料
│   ├── backup_database.sh    # 資料庫備份
│   ├── cleanup_logs.sh       # 日誌清理
│   └── deploy.sh             # 生產環境部署
│
├── dev-tools/                # 開發輔助工具
│   ├── generate_test_data.py # 產生測試資料
│   ├── mock_api.py           # API Mock 伺服器
│   └── db_seed.py            # 資料庫種子資料
│
├── deprecated/               # 已棄用腳本 (保留參考)
│   └── old_crawler.py        # 舊版 Python 爬蟲 (已遷移至 Go)
│
└── README.md                 # 腳本使用說明
```

### 常用腳本

| 腳本 | 用途 | 執行方式 |
|------|------|----------|
| `maintenance/update_moving_averages.sh` | 更新所有股票均線 | `./scripts/maintenance/update_moving_averages.sh` |
| `maintenance/backup_database.sh` | 備份 PostgreSQL 資料庫 | `./scripts/maintenance/backup_database.sh` |
| `dev-tools/generate_test_data.py` | 產生測試用股票資料 | `python scripts/dev-tools/generate_test_data.py` |

---

## 📚 Docs (專案文件)

**路徑**: `/docs/`  
**用途**: 專案開發、架構、維運文件集中管理

### 目錄結構

```
docs/
├── PROJECT_STRUCTURE.md      # 本檔案 - 資料夾結構說明
├── go-migration-plan.md      # Go 服務遷移計畫
├── go-implementation-status.md # Go 實作進度追蹤
├── automation-complete.md    # 自動化部署完成紀錄
├── optimize.md               # 效能優化建議與紀錄
│
└── archive/                  # 歷史文件歸檔
    ├── old_architecture.md   # 舊架構說明
    └── migration_logs/       # 遷移過程紀錄
```

### 文件說明

| 文件 | 用途 |
|------|------|
| `PROJECT_STRUCTURE.md` | 專案資料夾結構完整說明 (本檔案) |
| `go-migration-plan.md` | Python → Go 爬蟲遷移計畫，包含技術選型、時程規劃 |
| `go-implementation-status.md` | Go 服務實作進度，功能清單與完成狀態 |
| `automation-complete.md` | 自動化流程實作紀錄 (CI/CD、定時任務) |
| `optimize.md` | 效能優化建議，包含資料庫索引、快取策略 |

---

## 📦 Data (資料儲存)

**路徑**: `/data/`  
**用途**: Docker volumes 掛載點，持久化資料儲存

### 目錄結構

```
data/
├── postgres/                 # PostgreSQL 資料檔案
│   └── pgdata/               # 資料庫檔案 (由 Docker 管理)
│
├── redis/                    # Redis 資料檔案
│   └── dump.rdb              # Redis 持久化檔案
│
└── pgadmin/                  # pgAdmin 配置檔案
    └── config/
```

> ⚠️ **注意**: `/data/` 目錄已加入 `.gitignore`，不會提交至版本控制

---

## 📝 Logs (日誌檔案)

**路徑**: `/logs/`  
**用途**: 應用程式日誌輸出，依服務分類

### 目錄結構

```
logs/
├── backend/                  # FastAPI 後端日誌
│   ├── app.log               # 應用程式日誌
│   ├── celery.log            # Celery 任務日誌
│   └── error.log             # 錯誤日誌
│
├── crawler-service/          # Go 爬蟲日誌
│   ├── crawler.log           # 爬蟲執行日誌
│   └── error.log             # 錯誤日誌
│
└── frontend/                 # 前端日誌
    └── access.log            # Nginx 存取日誌
```

> ⚠️ **注意**: `/logs/` 目錄已加入 `.gitignore`，不會提交至版本控制

---

## 📤 Uploads (檔案上傳)

**路徑**: `/uploads/`  
**用途**: 使用者上傳檔案暫存區

### 目錄結構

```
uploads/
├── csv/                      # CSV 檔案上傳
├── images/                   # 圖片上傳
└── temp/                     # 臨時檔案 (定期清理)
```

> ⚠️ **注意**: `/uploads/` 目錄已加入 `.gitignore`，不會提交至版本控制

---

## 🐳 Docker 相關檔案

### docker-compose.yml

**路徑**: `/docker-compose.yml`  
**用途**: 本地開發環境服務編排

**定義服務**:
- `postgres` - PostgreSQL 15 資料庫 (port 9222)
- `redis` - Redis 快取 (port 9223)
- `backend` - FastAPI 後端服務 (port 9000)
- `frontend` - Nuxt.js 前端服務 (port 9100)
- `crawler-service` - Go 爬蟲服務 (port 9627)
- `celery-worker` - Celery 背景工作器
- `celery-beat` - Celery 定時任務排程器
- `pgadmin` - pgAdmin 資料庫管理工具 (port 9224)

**啟動方式**:
```bash
docker-compose up -d
```

### 環境變數檔案

| 檔案 | 用途 |
|------|------|
| `.env` | 本地開發環境變數 (不提交至 Git) |
| `.env.office` | 辦公室環境變數範本 |
| `.env.example` | 環境變數範例檔案 |

---

## 📖 其他重要檔案

| 檔案 | 用途 |
|------|------|
| `README.md` | 專案主要說明文件，快速開始指南 |
| `CLAUDE.md` | AI 開發助手 (Claude) 使用指引與上下文 |
| `USAGE_GUIDE.md` | 使用者操作手冊 |
| `restart.sh` | 快速重啟所有服務腳本 |

---

## 🔧 開發工具配置

### Makefile

各服務目錄下的 `Makefile` 提供常用指令封裝:

**Backend Makefile**:
```bash
make migrate        # 執行資料庫遷移
make test           # 執行測試
make lint           # 程式碼檢查
make run            # 啟動開發伺服器
```

**Crawler Service Makefile**:
```bash
make build          # 編譯 Go 程式
make test           # 執行測試
make run            # 啟動服務
make docker-build   # 建構 Docker 映像檔
```

---

## 🚀 快速開始

### 1. 啟動所有服務

```bash
# 根目錄執行
docker-compose up -d
```

### 2. 初始化資料庫

```bash
# 進入 backend 目錄
cd backend

# 執行資料庫遷移
make migrate

# 或手動執行
alembic upgrade head
```

### 3. 存取服務

- **前端**: http://localhost:9100
- **後端 API**: http://localhost:9000/docs (Swagger UI)
- **爬蟲服務**: http://localhost:9627/health
- **pgAdmin**: http://localhost:9224

---

## 📊 資料流向

```
┌─────────────────┐
│  Crawler Service │ (Go)
│   (Port 9627)    │
└────────┬────────┘
         │ 爬取股票資料
         │ 寫入資料庫
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   (Port 9222)   │
└────────┬────────┘
         │ 讀取資料
         ▼
┌─────────────────┐       ┌─────────────────┐
│  Backend (API)  │◄──────│  Celery Worker  │
│   (Port 9000)   │       │  (背景任務)      │
└────────┬────────┘       └─────────────────┘
         │ RESTful API
         ▼
┌─────────────────┐
│  Frontend (UI)  │
│   (Port 9100)   │
└─────────────────┘
         │
         ▼
     使用者瀏覽器
```

---

## 🎯 關鍵設計決策

### 1. 微服務架構

- **Backend (Python)**: 複雜業務邏輯、技術分析計算
- **Crawler (Go)**: 高效能資料爬取、大量並發處理
- **Frontend (Nuxt.js)**: SSR/SSG 支援、SEO 優化

### 2. 資料庫設計

- **PostgreSQL**: 主要資料儲存，支援複雜查詢與事務
- **Redis**: 快取層，減少資料庫負載

### 3. 背景任務

- **Celery**: 非同步任務處理 (均線計算、報表生成)
- **Celery Beat**: 定時任務排程 (每日資料更新)

### 4. 容器化部署

- **Docker Compose**: 本地開發環境一鍵啟動
- **多階段建構**: 減少最終映像檔大小

---

## 📝 維護建議

### 定期任務

1. **每日**:
   - 爬取最新股票資料 (由 Celery Beat 自動執行)
   - 更新技術指標與均線

2. **每週**:
   - 檢查日誌檔案大小，執行清理
   - 檢視系統效能監控數據

3. **每月**:
   - 資料庫備份與驗證
   - 檢查磁碟空間使用率
   - 更新依賴套件版本

### 監控指標

- **爬蟲服務**: 成功率、回應時間、錯誤類型
- **資料庫**: 連線數、查詢效能、儲存空間
- **API**: 請求量、回應時間、錯誤率

---

## 📞 聯絡資訊

如有問題或建議，請參考:
- **主要文件**: [README.md](../README.md)
- **API 文件**: [backend/API_DOCUMENTATION.md](../backend/API_DOCUMENTATION.md)
- **測試說明**: [backend/tests/README_INTEGRATION_TESTS.md](../backend/tests/README_INTEGRATION_TESTS.md)

---

> **更新紀錄**:  
> - 2026-01-11: 初版建立，包含完整專案結構說明
> - 2026-01-11: 新增 Go 爬蟲服務指標別名問題修復紀錄
