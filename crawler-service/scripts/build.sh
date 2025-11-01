#!/bin/bash
# 建構腳本
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "  建構 Go 爬蟲服務"
echo "=================================="

# 建立目錄
mkdir -p bin

# 取得版本資訊
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME=$(date -u '+%Y-%m-%d_%H:%M:%S')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${YELLOW}建構資訊:${NC}"
echo "  版本: $VERSION"
echo "  建構時間: $BUILD_TIME"
echo "  Git Commit: $GIT_COMMIT"
echo ""

# 設定建構參數
LDFLAGS="-X main.Version=$VERSION -X main.BuildTime=$BUILD_TIME -X main.GitCommit=$GIT_COMMIT"

# 建構
echo -e "${YELLOW}開始建構...${NC}"

# 當前平台
echo "建構當前平台版本..."
go build -ldflags "$LDFLAGS" -o bin/crawler-service ./cmd/crawler/main.go

# Linux (如果需要)
if [ "$1" = "linux" ] || [ "$1" = "all" ]; then
    echo "建構 Linux 版本..."
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "$LDFLAGS -w -s" -o bin/crawler-service-linux ./cmd/crawler/main.go
fi

# Darwin (如果需要)
if [ "$1" = "darwin" ] || [ "$1" = "all" ]; then
    echo "建構 macOS 版本..."
    CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build -ldflags "$LDFLAGS -w -s" -o bin/crawler-service-darwin ./cmd/crawler/main.go
fi

echo ""
echo -e "${GREEN}✓ 建構完成！${NC}"
echo ""
echo "產出檔案:"
ls -lh bin/crawler-service*
