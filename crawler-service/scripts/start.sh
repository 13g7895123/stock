#!/bin/bash
# Go 爬蟲服務啟動腳本
set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "  Go 爬蟲服務啟動腳本"
echo "=================================="

# 檢查環境變數檔案
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ 找到 .env 檔案${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠ 未找到 .env 檔案，使用預設配置${NC}"

    # 設定預設環境變數
    export DATABASE_URL="${DATABASE_URL:-postgresql://stock_user:password@localhost:9221/stock_analysis}"
    export SERVER_PORT="${SERVER_PORT:-8080}"
    export LOG_LEVEL="${LOG_LEVEL:-info}"
    export MAX_WORKERS="${MAX_WORKERS:-100}"
fi

# 檢查執行檔
if [ ! -f "bin/crawler-service" ]; then
    echo -e "${YELLOW}⚠ 執行檔不存在，開始建構...${NC}"
    make build || go build -o bin/crawler-service ./cmd/crawler/main.go
fi

# 檢查必要的環境變數
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ DATABASE_URL 環境變數未設定${NC}"
    echo "請設定 DATABASE_URL 或建立 .env 檔案"
    exit 1
fi

# 顯示配置資訊
echo ""
echo "配置資訊:"
echo "-----------------------------------"
echo "DATABASE_URL: $DATABASE_URL"
echo "SERVER_PORT: $SERVER_PORT"
echo "LOG_LEVEL: $LOG_LEVEL"
echo "MAX_WORKERS: $MAX_WORKERS"
echo ""

# 檢查資料庫連線
echo "檢查資料庫連線..."
if command -v psql &> /dev/null; then
    if psql "$DATABASE_URL" -c "SELECT 1" &> /dev/null; then
        echo -e "${GREEN}✓ 資料庫連線成功${NC}"
    else
        echo -e "${YELLOW}⚠ 無法連線到資料庫，服務可能無法正常運行${NC}"
        read -p "是否繼續啟動? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# 啟動服務
echo ""
echo "啟動服務..."
echo "=================================="

# 捕捉 Ctrl+C
trap 'echo -e "\n${YELLOW}正在關閉服務...${NC}"; exit 0' INT

# 執行服務
./bin/crawler-service
