#!/bin/bash
# ===========================================
# 股票分析系統 - 重啟腳本
# ===========================================
# 使用方式:
#   ./restart.sh          # 快速重啟 (僅重啟容器，適用於程式碼更新)
#   ./restart.sh --full   # 完整重啟 (重新載入 .env 和重建容器)
#   ./restart.sh --build  # 重新建置 (重建 Docker image)
#   ./restart.sh --help   # 顯示說明
# ===========================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 專案目錄
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

# 顯示標題
show_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}    股票分析系統 - 重啟工具${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# 顯示說明
show_help() {
    show_header
    echo -e "${GREEN}使用方式:${NC}"
    echo "  ./restart.sh              快速重啟 (僅重啟容器)"
    echo "  ./restart.sh --full       完整重啟 (重新載入 .env)"
    echo "  ./restart.sh --build      重新建置 (重建 Docker image)"
    echo "  ./restart.sh --service    重啟指定服務"
    echo "  ./restart.sh --help       顯示此說明"
    echo ""
    echo -e "${GREEN}參數說明:${NC}"
    echo -e "  ${YELLOW}(無參數)${NC}    - 快速重啟所有容器，適用於程式碼更新"
    echo -e "              程式碼變更會透過 volume mount 自動生效"
    echo ""
    echo -e "  ${YELLOW}--full${NC}      - 完整重啟，會重新讀取 .env 檔案"
    echo -e "              適用於環境變數或 PORT 配置變更"
    echo ""
    echo -e "  ${YELLOW}--build${NC}     - 重新建置所有 Docker image"
    echo -e "              適用於 Dockerfile 或 requirements.txt 變更"
    echo ""
    echo -e "  ${YELLOW}--service${NC}   - 重啟指定服務"
    echo -e "              例如: ./restart.sh --service backend"
    echo ""
    echo -e "${GREEN}可用服務:${NC}"
    echo "  backend, frontend, postgres, redis, celery_worker,"
    echo "  celery_beat, celery_flower, pgadmin, crawler-service"
    echo ""
}

# 檢查 Docker 狀態
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker 未運行，請先啟動 Docker${NC}"
        exit 1
    fi
}

# 顯示目前運行的容器
show_status() {
    echo -e "${BLUE}📊 目前容器狀態:${NC}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
    docker-compose ps 2>/dev/null
    echo ""
}

# 快速重啟 (restart)
quick_restart() {
    show_header
    echo -e "${YELLOW}🔄 快速重啟模式${NC}"
    echo -e "   適用於: 程式碼更新 (Python/Vue/Go)"
    echo -e "   注意: .env 變更不會生效"
    echo ""
    
    check_docker
    
    echo -e "${BLUE}⏳ 正在重啟所有容器...${NC}"
    docker compose restart
    
    echo ""
    echo -e "${GREEN}✅ 快速重啟完成！${NC}"
    echo ""
    show_status
}

# 完整重啟 (down + up)
full_restart() {
    show_header
    echo -e "${YELLOW}🔄 完整重啟模式${NC}"
    echo -e "   適用於: .env 環境變數變更、PORT 配置變更"
    echo ""
    
    check_docker
    
    echo -e "${BLUE}⏳ 正在停止所有容器...${NC}"
    docker compose down
    
    echo ""
    echo -e "${BLUE}⏳ 正在重新啟動容器 (載入最新 .env)...${NC}"
    docker compose up -d
    
    echo ""
    echo -e "${GREEN}✅ 完整重啟完成！${NC}"
    echo -e "${GREEN}   .env 配置已重新載入${NC}"
    echo ""
    
    # 等待服務啟動
    echo -e "${BLUE}⏳ 等待服務啟動...${NC}"
    sleep 5
    show_status
}

# 重新建置並啟動
build_restart() {
    show_header
    echo -e "${YELLOW}🔄 重新建置模式${NC}"
    echo -e "   適用於: Dockerfile、requirements.txt、package.json 變更"
    echo ""
    
    check_docker
    
    echo -e "${BLUE}⏳ 正在停止所有容器...${NC}"
    docker compose down
    
    echo ""
    echo -e "${BLUE}⏳ 正在重新建置並啟動容器...${NC}"
    docker compose up -d --build
    
    echo ""
    echo -e "${GREEN}✅ 重新建置完成！${NC}"
    echo ""
    
    # 等待服務啟動
    echo -e "${BLUE}⏳ 等待服務啟動...${NC}"
    sleep 10
    show_status
}

# 重啟指定服務
restart_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        echo -e "${RED}❌ 請指定服務名稱${NC}"
        echo "   例如: ./restart.sh --service backend"
        exit 1
    fi
    
    show_header
    echo -e "${YELLOW}🔄 重啟服務: ${service}${NC}"
    echo ""
    
    check_docker
    
    # 檢查服務是否存在
    if ! docker compose config --services 2>/dev/null | grep -q "^${service}$"; then
        echo -e "${RED}❌ 服務 '${service}' 不存在${NC}"
        echo ""
        echo -e "${BLUE}可用服務:${NC}"
        docker compose config --services 2>/dev/null
        exit 1
    fi
    
    echo -e "${BLUE}⏳ 正在重啟 ${service}...${NC}"
    docker compose restart "$service"
    
    echo ""
    echo -e "${GREEN}✅ 服務 ${service} 重啟完成！${NC}"
    echo ""
    
    # 顯示服務狀態
    docker compose ps "$service" --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# 主程式
main() {
    case "${1:-}" in
        --help|-h)
            show_help
            ;;
        --full|-f)
            full_restart
            ;;
        --build|-b)
            build_restart
            ;;
        --service|-s)
            restart_service "$2"
            ;;
        --status)
            show_header
            check_docker
            show_status
            ;;
        "")
            quick_restart
            ;;
        *)
            echo -e "${RED}❌ 未知參數: $1${NC}"
            echo "   使用 --help 查看說明"
            exit 1
            ;;
    esac
}

main "$@"
