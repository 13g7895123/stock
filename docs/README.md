# 📚 專案文件索引

> 完整的專案文件集中管理。選擇您需要的文檔類型開始閱讀。

---

## 🚀 新手入門

| 文檔 | 用途 | 時間 |
|------|------|------|
| [快速開始](guides/QUICK_START.md) | 5 分鐘內啟動完整系統 | ⏱️ 5 分鐘 |
| [使用指南](guides/USAGE_GUIDE.md) | 學習系統的各項功能 | ⏱️ 15 分鐘 |
| [專案結構](PROJECT_STRUCTURE.md) | 理解專案架構與組織 | ⏱️ 10 分鐘 |

## 🔧 技術文檔

### 後端 API (Python/FastAPI)

| 文檔 | 說明 |
|------|------|
| [API 完整文件](backend/API_DOCUMENTATION.md) | REST API 端點詳細說明、參數、回應格式 |
| [API 測試報告](backend/API_TEST_REPORT.md) | API 測試結果與覆蓋率 |
| [整合測試指南](backend/INTEGRATION_TESTS.md) | 執行整合測試的方法與配置 |

### 爬蟲服務 (Go)

| 文檔 | 說明 |
|------|------|
| [爬蟲服務完整指南](crawler/CRAWLER_SERVICE.md) | 架構、API 端點、最新修復紀錄 |
| [部署指南](crawler/DEPLOYMENT.md) | 三種部署方式詳細說明 |
| [Docker 指南](crawler/DOCKER_GUIDE.md) | Docker 使用與容器管理 |
| [儀表板指南](crawler/DASHBOARD_GUIDE.md) | 爬蟲監控儀表板使用方法 |
| [快速開始](crawler/QUICKSTART.md) | 爬蟲服務 5 分鐘快速上手 |

### 開發工具與腳本

| 文檔 | 說明 |
|------|------|
| [腳本使用指南](guides/SCRIPTS_GUIDE.md) | 維運與開發腳本使用方法 |

## 🐛 故障排除

| 文檔 | 說明 |
|------|------|
| [常見問題與解決方案](troubleshooting/COMMON_ISSUES.md) | 19 個常見問題的詳細解決步驟 |

## 📊 管理與監控

### 監控與日誌

1. **Prometheus**: http://localhost:9090 - 效能指標收集
2. **Grafana**: http://localhost:3000 - 可視化儀表板
3. **Flower**: http://localhost:5555 - Celery 任務監控
4. **pgAdmin**: http://localhost:9224 - PostgreSQL 管理

### 關鍵指標監控

```bash
# 爬蟲效能指標
curl http://localhost:9627/metrics

# API 健康檢查
curl http://localhost:9000/health

# 爬蟲健康檢查
curl http://localhost:9627/health
```

## 🎯 常見任務速查

### 我想...

<details>
<summary><b>啟動系統</b></summary>

```bash
docker-compose up -d
```

查看 [快速開始](guides/QUICK_START.md)

</details>

<details>
<summary><b>爬取股票資料</b></summary>

```bash
curl -X POST "http://localhost:9627/api/v1/stocks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330"]}'
```

查看 [使用指南](guides/USAGE_GUIDE.md#1-基本功能) 或 [爬蟲服務指南](crawler/CRAWLER_SERVICE.md#4-批次更新核心端點)

</details>

<details>
<summary><b>查詢 API</b></summary>

```bash
curl http://localhost:9000/api/v1/stocks
curl http://localhost:9000/docs  # Swagger UI
```

查看 [API 文件](backend/API_DOCUMENTATION.md)

</details>

<details>
<summary><b>部署到生產環境</b></summary>

查看 [爬蟲部署指南](crawler/DEPLOYMENT.md)

</details>

<details>
<summary><b>排除故障</b></summary>

查看 [常見問題](troubleshooting/COMMON_ISSUES.md)

</details>

<details>
<summary><b>監控系統效能</b></summary>

1. Prometheus: http://localhost:9090
2. Grafana: http://localhost:3000
3. Flower: http://localhost:5555

查看各服務文檔的監控章節

</details>

<details>
<summary><b>查看系統架構</b></summary>

查看 [專案結構](PROJECT_STRUCTURE.md)

</details>

## 📋 文檔組織結構

```
docs/
├── README.md                  # 本檔案 - 文件索引
├── PROJECT_STRUCTURE.md       # 完整的專案架構說明
│
├── guides/                    # 使用與開發指南
│   ├── QUICK_START.md         # 快速開始（5 分鐘）
│   ├── USAGE_GUIDE.md         # 詳細使用指南
│   ├── SCRIPTS_GUIDE.md       # 腳本工具使用方法
│   └── DEVELOPER_GUIDE.md     # 開發指南（規劃中）
│
├── backend/                   # 後端文檔
│   ├── API_DOCUMENTATION.md   # REST API 完整文件
│   ├── API_TEST_REPORT.md     # 測試報告
│   └── INTEGRATION_TESTS.md   # 整合測試說明
│
├── crawler/                   # 爬蟲服務文檔
│   ├── CRAWLER_SERVICE.md     # 完整指南（最重要）
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── DOCKER_GUIDE.md        # Docker 使用
│   ├── DASHBOARD_GUIDE.md     # 儀表板指南
│   ├── QUICKSTART.md          # 5 分鐘快速開始
│   └── START-HERE.md          # 入門指南
│
├── troubleshooting/           # 故障排除
│   ├── COMMON_ISSUES.md       # 19 個常見問題與解決
│   └── FAQ.md                 # 常見問題（規劃中）
│
└── archive/                   # 歷史文件
    ├── go-migration-plan.md   # Go 遷移計畫
    ├── go-implementation-status.md # 實作進度
    ├── automation-complete.md # 自動化部署完成紀錄
    ├── optimize.md            # 效能優化
    └── ...                    # 其他舊文檔
```

## 🔗 快速連結

### 服務端點

| 服務 | URL | 說明 |
|------|-----|------|
| 前端 | http://localhost:3000 | Vue/Nuxt 主應用 |
| 後端 API | http://localhost:9000 | REST API 伺服器 |
| API 文件 | http://localhost:9000/docs | Swagger UI |
| 爬蟲服務 | http://localhost:9627 | Go 爬蟲儀表板 |
| 資料庫管理 | http://localhost:9224 | pgAdmin |
| 任務監控 | http://localhost:5555 | Celery Flower |
| Prometheus | http://localhost:9090 | 指標收集 |
| Grafana | http://localhost:3000 | 可視化儀表板 |

### GitHub 相關

- **Repository**: [stock](https://github.com/13g7895123/stock)
- **Issues**: 反饋問題與建議
- **Pull Requests**: 查看開發進度

## 📞 獲取幫助

1. **基本問題** → 查看 [快速開始](guides/QUICK_START.md)
2. **功能使用** → 查看 [使用指南](guides/USAGE_GUIDE.md)
3. **API 相關** → 查看 [API 文件](backend/API_DOCUMENTATION.md)
4. **爬蟲相關** → 查看 [爬蟲指南](crawler/CRAWLER_SERVICE.md)
5. **故障排除** → 查看 [常見問題](troubleshooting/COMMON_ISSUES.md)

## 🆕 最新更新

### 2026-01-11 修復

✅ **修復 Go 爬蟲資料重複問題**
- 根本原因: range loop 指標別名
- 影響: 股票 2330 所有記錄顯示相同價格
- 解決: 在 `stock_service.go` 建立本地副本後取址
- 驗證: 資料庫現已包含正確的變動價格

詳見 [爬蟲服務指南 - 核心代碼走查](crawler/CRAWLER_SERVICE.md#2-stock-service-層internal-service-stock_servicego)

### 2026-01-11 文件整理

✅ **集中管理所有專案文檔至 /docs 目錄**

新建檔案：
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 專案完整架構
- [guides/QUICK_START.md](guides/QUICK_START.md) - 快速開始指南
- [guides/USAGE_GUIDE.md](guides/USAGE_GUIDE.md) - 詳細使用指南
- [crawler/CRAWLER_SERVICE.md](crawler/CRAWLER_SERVICE.md) - 爬蟲完整指南
- [troubleshooting/COMMON_ISSUES.md](troubleshooting/COMMON_ISSUES.md) - 常見問題解決

整理檔案：
- 複製所有 markdown 檔案至 docs 各子目錄
- 建立統一的文件索引和導航

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
