#!/bin/bash
# 一鍵部署腳本 - 自動完成所有設定和啟動
set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo -e "${BLUE}  Go 爬蟲服務一鍵部署腳本${NC}"
echo "========================================="

# 選單
show_menu() {
    echo ""
    echo "請選擇部署方式："
    echo "  1) Docker 部署（推薦）- 自動設定所有服務"
    echo "  2) 本機部署 - 在本機直接執行"
    echo "  3) 僅建構 - 只建構不執行"
    echo "  4) 停止服務"
    echo "  5) 查看日誌"
    echo "  6) 健康檢查"
    echo "  0) 退出"
    echo ""
}

# 檢查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker 未安裝${NC}"
        echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
        return 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker 服務未啟動${NC}"
        echo "請啟動 Docker 服務"
        return 1
    fi

    echo -e "${GREEN}✓ Docker 已就緒${NC}"
    return 0
}

# 檢查 docker-compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}✗ docker-compose 未安裝${NC}"
        echo "請安裝 docker-compose"
        return 1
    fi

    echo -e "${GREEN}✓ docker-compose 已就緒${NC}"
    return 0
}

# 建立 .env 檔案
setup_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}建立 .env 檔案...${NC}"

        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✓ 已從 .env.example 建立 .env${NC}"
        else
            # 建立基本的 .env
            cat > .env << EOF
DATABASE_URL=postgresql://stock_user:password@postgres:5432/stock_analysis
POSTGRES_DB=stock_analysis
POSTGRES_USER=stock_user
POSTGRES_PASSWORD=password
GO_CRAWLER_PORT=8080
LOG_LEVEL=info
MAX_WORKERS=100
EOF
            echo -e "${GREEN}✓ 已建立預設 .env${NC}"
        fi

        echo -e "${YELLOW}請檢查並修改 .env 檔案中的配置${NC}"
        read -p "按 Enter 繼續..."
    else
        echo -e "${GREEN}✓ .env 檔案已存在${NC}"
    fi
}

# Docker 部署
deploy_docker() {
    echo ""
    echo "========================================="
    echo -e "${BLUE}  Docker 部署${NC}"
    echo "========================================="

    # 檢查環境
    check_docker || exit 1
    check_docker_compose || exit 1

    # 設定環境變數
    setup_env

    # 載入環境變數
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi

    cd deployments

    echo ""
    echo -e "${YELLOW}步驟 1: 停止舊服務（如果有）${NC}"
    docker-compose down 2>/dev/null || true

    echo ""
    echo -e "${YELLOW}步驟 2: 建構映像${NC}"
    docker-compose build --no-cache

    echo ""
    echo -e "${YELLOW}步驟 3: 啟動服務${NC}"
    docker-compose up -d

    echo ""
    echo -e "${YELLOW}步驟 4: 等待服務啟動...${NC}"
    sleep 10

    echo ""
    echo -e "${YELLOW}步驟 5: 檢查服務狀態${NC}"
    docker-compose ps

    echo ""
    echo "========================================="
    echo -e "${GREEN}  部署完成！${NC}"
    echo "========================================="
    echo ""
    echo "服務訪問："
    echo "  • Go 爬蟲服務: http://localhost:${GO_CRAWLER_PORT:-8080}"
    echo "  • 健康檢查: http://localhost:${GO_CRAWLER_PORT:-8080}/health"
    echo "  • Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
    echo "  • Grafana: http://localhost:${GRAFANA_PORT:-3001} (admin/admin)"
    echo ""
    echo "常用命令："
    echo "  • 查看日誌: docker-compose -f deployments/docker-compose.yml logs -f"
    echo "  • 停止服務: docker-compose -f deployments/docker-compose.yml down"
    echo "  • 重啟服務: docker-compose -f deployments/docker-compose.yml restart"
    echo ""
}

# 本機部署
deploy_local() {
    echo ""
    echo "========================================="
    echo -e "${BLUE}  本機部署${NC}"
    echo "========================================="

    # 檢查 Go
    if ! command -v go &> /dev/null; then
        echo -e "${RED}✗ Go 未安裝${NC}"
        echo "執行安裝腳本: ./scripts/install.sh"
        exit 1
    fi

    echo -e "${GREEN}✓ Go 已安裝${NC}"

    # 設定環境變數
    setup_env

    echo ""
    echo -e "${YELLOW}步驟 1: 下載依賴${NC}"
    go mod download
    go mod tidy

    echo ""
    echo -e "${YELLOW}步驟 2: 建構應用程式${NC}"
    ./scripts/build.sh

    echo ""
    echo -e "${YELLOW}步驟 3: 啟動服務${NC}"
    echo "使用 Ctrl+C 停止服務"
    echo ""

    ./scripts/start.sh
}

# 僅建構
build_only() {
    echo ""
    echo "========================================="
    echo -e "${BLUE}  建構應用程式${NC}"
    echo "========================================="

    read -p "選擇建構方式 (1=本機, 2=Docker): " choice

    case $choice in
        1)
            if ! command -v go &> /dev/null; then
                echo -e "${RED}✗ Go 未安裝${NC}"
                exit 1
            fi
            ./scripts/build.sh
            ;;
        2)
            check_docker || exit 1
            cd deployments
            docker-compose build
            ;;
        *)
            echo -e "${RED}無效的選擇${NC}"
            ;;
    esac
}

# 停止服務
stop_services() {
    echo ""
    echo -e "${YELLOW}停止服務...${NC}"

    read -p "選擇要停止的服務 (1=Docker, 2=本機, 3=全部): " choice

    case $choice in
        1)
            cd deployments
            docker-compose down
            echo -e "${GREEN}✓ Docker 服務已停止${NC}"
            ;;
        2)
            pkill -f "crawler-service" || true
            echo -e "${GREEN}✓ 本機服務已停止${NC}"
            ;;
        3)
            cd deployments
            docker-compose down
            pkill -f "crawler-service" || true
            echo -e "${GREEN}✓ 所有服務已停止${NC}"
            ;;
        *)
            echo -e "${RED}無效的選擇${NC}"
            ;;
    esac
}

# 查看日誌
view_logs() {
    echo ""
    echo -e "${YELLOW}查看日誌...${NC}"

    read -p "選擇服務 (1=Go爬蟲, 2=Postgres, 3=全部): " choice

    cd deployments

    case $choice in
        1)
            docker-compose logs -f crawler-service
            ;;
        2)
            docker-compose logs -f postgres
            ;;
        3)
            docker-compose logs -f
            ;;
        *)
            echo -e "${RED}無效的選擇${NC}"
            ;;
    esac
}

# 健康檢查
health_check() {
    echo ""
    echo "========================================="
    echo -e "${BLUE}  健康檢查${NC}"
    echo "========================================="

    # 檢查 Docker 服務
    if docker ps | grep -q "stock-crawler-go"; then
        echo -e "${GREEN}✓ Docker 服務運行中${NC}"

        # 檢查健康狀態
        echo ""
        echo "容器狀態："
        docker ps --filter "name=stock-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

        # 檢查健康端點
        echo ""
        echo "健康端點檢查："
        if curl -sf http://localhost:${GO_CRAWLER_PORT:-8080}/health > /dev/null; then
            echo -e "${GREEN}✓ Go 爬蟲服務健康${NC}"
            curl -s http://localhost:${GO_CRAWLER_PORT:-8080}/health | jq . 2>/dev/null || curl -s http://localhost:${GO_CRAWLER_PORT:-8080}/health
        else
            echo -e "${RED}✗ Go 爬蟲服務無回應${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Docker 服務未運行${NC}"
    fi

    # 檢查本機服務
    echo ""
    if pgrep -f "crawler-service" > /dev/null; then
        echo -e "${GREEN}✓ 本機服務運行中${NC}"
    else
        echo -e "${YELLOW}⚠ 本機服務未運行${NC}"
    fi
}

# 主選單
main() {
    while true; do
        show_menu
        read -p "請選擇 [0-6]: " choice

        case $choice in
            1)
                deploy_docker
                read -p "按 Enter 返回選單..."
                ;;
            2)
                deploy_local
                read -p "按 Enter 返回選單..."
                ;;
            3)
                build_only
                read -p "按 Enter 返回選單..."
                ;;
            4)
                stop_services
                read -p "按 Enter 返回選單..."
                ;;
            5)
                view_logs
                ;;
            6)
                health_check
                read -p "按 Enter 返回選單..."
                ;;
            0)
                echo -e "${GREEN}再見！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}無效的選擇，請重新輸入${NC}"
                ;;
        esac
    done
}

# 執行
main
