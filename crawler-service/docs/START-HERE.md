# 🚀 從這裡開始

## 只需三步，啟動 Go 爬蟲服務！

### 步驟 1: 進入專案目錄

```bash
cd crawler-service/
```

### 步驟 2: 執行一鍵部署腳本

```bash
./scripts/deploy.sh
```

### 步驟 3: 選擇部署方式

腳本會顯示選單：

```
請選擇部署方式：
  1) Docker 部署（推薦）⭐
  2) 本機部署
  3) 僅建構
```

**選擇 1** 即可！

---

## 就這麼簡單！ 🎉

等待幾分鐘後，服務就會自動啟動。

### 驗證服務

```bash
# 健康檢查
curl http://localhost:8080/health

# 預期回應
{"status":"ok"}
```

### 訪問服務

- **Go 爬蟲服務**: http://localhost:8080
- **Prometheus 監控**: http://localhost:9090
- **Grafana 儀表板**: http://localhost:3001 (admin/admin)

---

## 需要幫助？

### 📖 查看文檔

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - 詳細部署指南
- **[QUICKSTART.md](QUICKSTART.md)** - 5 分鐘快速開始
- **[README.md](README.md)** - 專案說明

### 🛠 管理服務

再次執行部署腳本即可管理服務：

```bash
./scripts/deploy.sh
```

選單選項：
- 1 - 部署服務
- 4 - 停止服務
- 5 - 查看日誌
- 6 - 健康檢查

### 🐛 遇到問題？

1. 執行健康檢查：`./scripts/deploy.sh` → 選擇 6
2. 查看日誌：`./scripts/deploy.sh` → 選擇 5
3. 參考文檔：`DEPLOYMENT.md`

---

## 常見問題

**Q: 沒有 Docker 怎麼辦？**
A: 選擇「2) 本機部署」，腳本會自動安裝 Go 和依賴

**Q: 埠號衝突怎麼辦？**
A: 編輯 `.env` 檔案修改埠號

**Q: 如何停止服務？**
A: 執行 `./scripts/deploy.sh` 選擇「4) 停止服務」

---

**立即開始：**

```bash
cd crawler-service/
./scripts/deploy.sh
```

**祝您使用愉快！** 🎈
