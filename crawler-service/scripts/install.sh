#!/bin/bash
# Go 爬蟲服務安裝腳本
set -e

echo "=================================="
echo "  Go 爬蟲服務安裝腳本"
echo "=================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查作業系統
OS="$(uname -s)"
ARCH="$(uname -m)"

echo -e "${GREEN}檢測到系統: $OS $ARCH${NC}"

# 設定 Go 版本
GO_VERSION="1.21.5"

# 檢查 Go 是否已安裝
check_go() {
    if command -v go &> /dev/null; then
        INSTALLED_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
        echo -e "${GREEN}✓ Go 已安裝 (版本: $INSTALLED_VERSION)${NC}"

        # 檢查版本是否符合要求
        if [ "$(printf '%s\n' "$GO_VERSION" "$INSTALLED_VERSION" | sort -V | head -n1)" = "$GO_VERSION" ]; then
            echo -e "${GREEN}✓ Go 版本符合要求${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Go 版本過舊，需要 $GO_VERSION 或更高版本${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}✗ Go 未安裝${NC}"
        return 1
    fi
}

# 安裝 Go
install_go() {
    echo -e "${YELLOW}開始安裝 Go $GO_VERSION...${NC}"

    # 確定下載 URL
    case $OS in
        Linux)
            case $ARCH in
                x86_64)
                    GO_TAR="go${GO_VERSION}.linux-amd64.tar.gz"
                    ;;
                aarch64)
                    GO_TAR="go${GO_VERSION}.linux-arm64.tar.gz"
                    ;;
                *)
                    echo -e "${RED}不支援的架構: $ARCH${NC}"
                    exit 1
                    ;;
            esac
            ;;
        Darwin)
            case $ARCH in
                x86_64)
                    GO_TAR="go${GO_VERSION}.darwin-amd64.tar.gz"
                    ;;
                arm64)
                    GO_TAR="go${GO_VERSION}.darwin-arm64.tar.gz"
                    ;;
                *)
                    echo -e "${RED}不支援的架構: $ARCH${NC}"
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo -e "${RED}不支援的作業系統: $OS${NC}"
            exit 1
            ;;
    esac

    GO_URL="https://go.dev/dl/$GO_TAR"

    # 下載 Go
    echo "下載 Go from $GO_URL..."
    cd /tmp
    wget -q --show-progress "$GO_URL" || {
        echo -e "${RED}下載失敗${NC}"
        exit 1
    }

    # 解壓
    echo "解壓 Go..."
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "$GO_TAR"
    rm "$GO_TAR"

    # 設定環境變數
    if ! grep -q "/usr/local/go/bin" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Go 環境變數" >> ~/.bashrc
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        echo 'export GOPATH=$HOME/go' >> ~/.bashrc
        echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
    fi

    # 立即生效
    export PATH=$PATH:/usr/local/go/bin
    export GOPATH=$HOME/go
    export PATH=$PATH:$GOPATH/bin

    echo -e "${GREEN}✓ Go 安裝完成${NC}"
}

# 安裝開發工具
install_dev_tools() {
    echo -e "${YELLOW}安裝開發工具...${NC}"

    # golangci-lint
    if ! command -v golangci-lint &> /dev/null; then
        echo "安裝 golangci-lint..."
        go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
    fi

    # goimports
    if ! command -v goimports &> /dev/null; then
        echo "安裝 goimports..."
        go install golang.org/x/tools/cmd/goimports@latest
    fi

    echo -e "${GREEN}✓ 開發工具安裝完成${NC}"
}

# 下載專案依賴
install_dependencies() {
    echo -e "${YELLOW}下載專案依賴...${NC}"

    cd "$(dirname "$0")/.."

    if [ -f "go.mod" ]; then
        go mod download
        go mod tidy
        echo -e "${GREEN}✓ 依賴下載完成${NC}"
    else
        echo -e "${RED}✗ 找不到 go.mod 檔案${NC}"
        exit 1
    fi
}

# 建構應用程式
build_app() {
    echo -e "${YELLOW}建構應用程式...${NC}"

    cd "$(dirname "$0")/.."

    # 建立 bin 目錄
    mkdir -p bin

    # 建構
    go build -o bin/crawler-service ./cmd/crawler/main.go

    if [ -f "bin/crawler-service" ]; then
        echo -e "${GREEN}✓ 建構成功${NC}"
        echo -e "${GREEN}執行檔位置: bin/crawler-service${NC}"
    else
        echo -e "${RED}✗ 建構失敗${NC}"
        exit 1
    fi
}

# 主流程
main() {
    echo ""
    echo "步驟 1: 檢查 Go 環境"
    echo "-----------------------------------"

    if check_go; then
        echo -e "${GREEN}Go 環境已就緒${NC}"
    else
        read -p "是否安裝 Go? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_go
        else
            echo -e "${RED}取消安裝${NC}"
            exit 1
        fi
    fi

    echo ""
    echo "步驟 2: 安裝開發工具"
    echo "-----------------------------------"
    install_dev_tools

    echo ""
    echo "步驟 3: 下載專案依賴"
    echo "-----------------------------------"
    install_dependencies

    echo ""
    echo "步驟 4: 建構應用程式"
    echo "-----------------------------------"
    build_app

    echo ""
    echo "=================================="
    echo -e "${GREEN}  安裝完成！${NC}"
    echo "=================================="
    echo ""
    echo "下一步："
    echo "  1. 設定環境變數（參考 .env.example）"
    echo "  2. 執行服務：./bin/crawler-service"
    echo "  或使用啟動腳本：./scripts/start.sh"
    echo ""
}

# 執行主流程
main
