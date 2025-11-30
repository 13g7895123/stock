# 台股分析系統 (Stock Analysis System)

台股資料收集、技術分析與智能選股系統，採用現代化微服務架構。

## 📁 專案結構

```
stock/
├── backend/                    # Python FastAPI 後端服務
│   ├── src/
│   │   ├── api/               # API 端點定義
│   │   ├── core/              # 核心配置 (資料庫、設定)
│   │   ├── models/            # SQLAlchemy 資料模型
│   │   ├── services/          # 業務邏輯服務層
│   │   ├── schemas/           # Pydantic 資料驗證
│   │   ├── utils/             # 工具函數
│   │   └── celery_app/        # Celery 背景任務
│   ├── tests/                 # 測試套件
│   └── alembic/               # 資料庫遷移
│
├── frontend/                   # Nuxt.js 前端應用
│   ├── pages/                 # 頁面元件
│   ├── components/            # 共用元件
│   ├── composables/           # 組合式函數
│   ├── stores/                # Pinia 狀態管理
│   └── tests/                 # 前端測試
│
├── crawler-service/           # Go 爬蟲服務
│   ├── cmd/                   # 程式進入點
│   ├── internal/              # 內部模組
│   └── pkg/                   # 公開套件
│
├── scripts/                   # 腳本工具
│   ├── maintenance/           # 維運腳本 (均線更新、部署等)
│   ├── dev-tools/             # 開發輔助工具
│   └── deprecated/            # 已棄用腳本 (保留參考)
│
├── docs/                      # 專案文件
│   ├── go-migration-plan.md   # Go 遷移計畫
│   ├── go-implementation-status.md
│   └── archive/               # 歷史文件
│
├── data/                      # 資料儲存 (Docker volumes)
├── logs/                      # 應用程式日誌
├── uploads/                   # 上傳檔案暫存
│
├── docker-compose.yml         # Docker 服務編排
├── .env                       # 環境變數 (不提交)
├── .env.office                # 辦公室環境變數
├── CLAUDE.md                  # AI 開發助手指引
└── USAGE_GUIDE.md             # 使用者操作指南
```

## 🚀 快速開始

### 環境需求
- Docker & Docker Compose
- (選用) Python 3.11+, Node.js 20+, Go 1.21+

### 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

### 服務端點

| 服務 | 端口 | 說明 |
|------|------|------|
| **Frontend** | http://localhost:3000 | 前端 Web 應用 |
| **Backend API** | http://localhost:9127 | REST API |
| **API Docs** | http://localhost:9127/docs | Swagger 文件 |
| **PostgreSQL** | localhost:9227 | 資料庫 |
| **Redis** | localhost:9327 | 快取/訊息佇列 |
| **Celery Flower** | http://localhost:9427 | 任務監控 |
| **PgAdmin** | http://localhost:9527 | 資料庫管理 |

## 📊 核心功能

### 股票資料
- 每日收盤資料自動更新
- 多資料來源整合 (證交所、Yahoo Finance)
- 歷史資料查詢與匯出

### 技術分析
- **均線計算**: MA5, MA10, MA20, MA72, MA120, MA240
- **選股策略**:
  - 完美多頭: MA5 > MA10 > MA20 > MA60 > MA120 > MA240
  - 短線多頭: MA5 > MA10 > MA20
  - 空頭趨勢: MA5 < MA10 < MA20 < MA60

### 背景任務
- 自動資料更新排程
- 均線批次計算
- 任務執行記錄與監控

## 🛠 維運腳本

```bash
# 均線批次更新
./scripts/maintenance/fast_update_ma.sh

# 查看更新進度
./scripts/maintenance/check_ma_progress.sh

# 部署新功能
./scripts/maintenance/apply_new_features.sh
```

## 📖 API 文件

完整 API 文件請參考:
- Swagger UI: http://localhost:9127/docs
- 詳細說明: [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)

### 主要 API 端點

| 端點 | 說明 |
|------|------|
| `GET /api/v1/health` | 健康檢查 |
| `GET /api/v1/stocks` | 股票清單 |
| `GET /api/v1/stock-history/{code}` | 歷史資料 |
| `GET /api/v1/moving-averages/{code}` | 均線資料 |
| `GET /api/v1/stock-selection/results` | 選股結果 |

## 🧪 測試

```bash
# 後端測試
cd backend && pytest -v

# 前端測試
cd frontend && npm run test
```

## 📝 開發指南

### 新增 API 端點
1. 在 `backend/src/api/endpoints/` 建立端點檔案
2. 在 `backend/src/services/` 實作業務邏輯
3. 在 `backend/src/api/router.py` 註冊路由
4. 撰寫測試於 `backend/tests/`

### 新增前端頁面
1. 在 `frontend/pages/` 建立 Vue 元件
2. 使用 `frontend/composables/` 的共用邏輯
3. 撰寫測試於 `frontend/tests/`

## 🔧 常見問題

### 容器無法啟動
```bash
docker-compose down -v
docker-compose up -d --build
```

### 資料庫連線失敗
```bash
docker-compose restart postgres
docker-compose logs postgres
```

### 清理快取
```bash
# 清理 Python 快取
find . -name "__pycache__" -type d -exec rm -rf {} +

# 清理前端快取
rm -rf frontend/.nuxt frontend/node_modules/.cache
```

## 📄 授權

私有專案 - 未經授權請勿散布
