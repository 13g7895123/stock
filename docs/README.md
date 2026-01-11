# 📚 專案文件索引

> 完整的專案文件集中管理。選擇您需要的文檔類型開始閱讀。

---

# 📚 Stock Crawler Service - 文件中心

> 高效能台灣股票資料爬蟲服務完整文件

---

## 🚀 新手入門

| 文檔 | 用途 | 時間 |
|------|------|------|
| [快速開始](QUICK_START.md) | 5 分鐘內啟動爬蟲服務 | ⏱️ 5 分鐘 |
| [專案結構](PROJECT_STRUCTURE.md) | 理解專案架構與組織 | ⏱️ 10 分鐘 |

## 🔧 爬蟲服務文檔

| 文檔 | 說明 |
|------|------|
| [爬蟲服務完整指南](crawler/CRAWLER_SERVICE.md) | 架構、API 端點、最新修復紀錄 |
| [部署指南](crawler/DEPLOYMENT.md) | 三種部署方式詳細說明 |
| [Docker 指南](crawler/DOCKER_GUIDE.md) | Docker 使用與容器管理 |
| [儀表板指南](crawler/DASHBOARD_GUIDE.md) | 爬蟲監控儀表板使用方法 |
| [API 文件](crawler/API.md) | RESTful API 完整說明 |
| [快速開始](crawler/QUICKSTART.md) | 爬蟲服務 5 分鐘快速上手 |

## 📊 管理與監控

### 服務端點

| 服務 | URL | 說明 |
|------|-----|------|
| 爬蟲服務 | http://localhost:9627 | Go 爬蟲儀表板與 API |
| 資料庫 | localhost:9222 | PostgreSQL (使用 psql 連線) |
| Prometheus | http://localhost:9627/metrics | 效能指標 |

### 關鍵指標監控

```bash
# 爬蟲效能指標
curl http://localhost:9627/metrics

# 健康檢查
curl http://localhost:9627/health
```

## 🎯 常見任務速查

### 我想...

<details>
<summary><b>啟動系統</b></summary>

```bash
docker-compose up -d
```

查看 [快速開始](QUICK_START.md)

</details>

<details>
<summary><b>爬取股票資料</b></summary>

```bash
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'
```

查看 [爬蟲服務指南](crawler/CRAWLER_SERVICE.md#4-批次更新核心端點)

</details>

<details>
<summary><b>查詢 API</b></summary>

```bash
curl http://localhost:9627/api/v1/stocks
```

查看 [API 文件](crawler/API.md)

</details>

<details>
<summary><b>部署到生產環境</b></summary>

查看 [爬蟲部署指南](crawler/DEPLOYMENT.md)

</details>

<details>
<summary><b>監控系統效能</b></summary>

```bash
# 查看 Prometheus 指標
curl http://localhost:9627/metrics

# 查看日誌
docker-compose logs -f crawler-service
```

</details>

<details>
<summary><b>查看系統架構</b></summary>

查看 [專案結構](PROJECT_STRUCTURE.md)

</details>

## 📋 文檔組織結構

```
docs/
├── README.md                  # 本檔案 - 文件索引
├── QUICK_START.md             # 快速開始（5 分鐘）
├── PROJECT_STRUCTURE.md       # 完整的專案架構說明
│
├── crawler/                   # 爬蟲服務文檔
│   ├── CRAWLER_SERVICE.md     # 完整指南（最重要）
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── DOCKER_GUIDE.md        # Docker 使用
│   ├── DASHBOARD_GUIDE.md     # 儀表板指南
│   ├── QUICKSTART.md          # 5 分鐘快速開始
│   ├── API.md                 # API 文件
│   └── START-HERE.md          # 入門指南
│
└── archive/                   # 歷史文件
    ├── go-migration-plan.md   # Go 遷移計畫
    ├── go-implementation-status.md # 實作進度
    ├── automation-complete.md # 自動化部署完成紀錄
    ├── optimize.md            # 效能優化
    └── ORGANIZATION_REPORT.md # 文件整理報告
```

## 🔗 快速連結

### 服務端點

| 服務 | URL | 說明 |
|------|-----|------|
| 爬蟲服務 | http://localhost:9627 | Go 爬蟲儀表板 |
| 爬蟲 API | http://localhost:9627/api/v1 | RESTful API |
| 資料庫 | localhost:9222 | PostgreSQL |
| Prometheus | http://localhost:9627/metrics | 效能指標 |

### GitHub 相關

- **Repository**: [stock](https://github.com/13g7895123/stock)
- **Issues**: 反饋問題與建議
- **Pull Requests**: 查看開發進度

## 📞 獲取幫助

1. **基本問題** → 查看 [快速開始](QUICK_START.md)
2. **爬蟲相關** → 查看 [爬蟲指南](crawler/CRAWLER_SERVICE.md)
3. **部署問題** → 查看 [部署指南](crawler/DEPLOYMENT.md)
4. **API 使用** → 查看 [API 文件](crawler/API.md)

## 🆕 最新更新

### 2026-01-11 專案重構

✅ **簡化專案結構**
- 移除後端服務 (Python/FastAPI) → `_old/backend/`
- 移除前端服務 (Nuxt.js) → `_old/frontend/`
- 移除舊腳本與文檔 → `_old/`
- **只保留 Go 爬蟲核心服務**

✅ **Docker Compose 簡化**
- 只保留 `postgres` + `crawler-service` 兩個服務
- 移除 Redis, Celery, pgAdmin 等不必要服務
- 啟動時間從 60 秒降至 15 秒

✅ **文檔重整**
- 重寫 README.md 聚焦於爬蟲服務
- 簡化文檔結構，只保留爬蟲相關
- 更新所有文檔連結與導航

✅ **修復 Go 爬蟲資料重複問題**
- 根本原因: range loop 指標別名
- 影響: 股票 2330 所有記錄顯示相同價格
- 解決: 在 `stock_service.go` 建立本地副本後取址

詳見 [爬蟲服務指南](crawler/CRAWLER_SERVICE.md#2-stock-service-層)

## 📝 文檔貢獻

如發現文檔錯誤或有改進建議，歡迎：
1. 提交 Issue
2. 提交 Pull Request
3. 聯絡開發團隊

## 📄 文檔版本

- **當前版本**: v1.0.0
- **更新日期**: 2026-01-11
- **維護者**: 開發團隊

---

**提示**: 使用 `Ctrl+F` (或 `Cmd+F`) 搜尋文件內容，快速找到您需要的信息。
