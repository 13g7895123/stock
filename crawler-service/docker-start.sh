#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   股票爬虫服务 - Docker 快速启动脚本${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker 运行正常${NC}"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 显示菜单
echo -e "${YELLOW}请选择操作:${NC}"
echo "  1) 启动服务"
echo "  2) 停止服务"
echo "  3) 重启服务"
echo "  4) 查看状态"
echo "  5) 查看日志"
echo "  6) 重新构建并启动"
echo "  7) 初始化数据库表"
echo "  8) 爬取测试数据"
echo "  9) 打开监控面板"
echo "  0) 退出"
echo ""
read -p "输入选项 (0-9): " choice

case $choice in
    1)
        echo -e "${BLUE}🚀 启动服务...${NC}"
        docker compose up -d
        echo ""
        echo -e "${GREEN}✅ 服务已启动！${NC}"
        echo -e "   监控面板: ${BLUE}http://localhost:9627${NC}"
        ;;
    2)
        echo -e "${BLUE}⏹️  停止服务...${NC}"
        docker compose down
        echo -e "${GREEN}✅ 服务已停止${NC}"
        ;;
    3)
        echo -e "${BLUE}🔄 重启服务...${NC}"
        docker compose restart
        echo -e "${GREEN}✅ 服务已重启${NC}"
        ;;
    4)
        echo -e "${BLUE}📊 服务状态:${NC}"
        docker compose ps
        echo ""
        echo -e "${BLUE}健康检查:${NC}"
        curl -s http://localhost:9627/health | head -c 200
        echo ""
        ;;
    5)
        echo -e "${BLUE}📜 查看日志 (Ctrl+C 退出):${NC}"
        docker compose logs -f
        ;;
    6)
        echo -e "${BLUE}🔨 重新构建镜像...${NC}"
        docker build -t stock-crawler-service:latest -f deployments/Dockerfile .
        echo ""
        echo -e "${BLUE}🚀 启动服务...${NC}"
        docker compose down
        docker compose up -d
        echo -e "${GREEN}✅ 重新构建并启动完成！${NC}"
        ;;
    7)
        echo -e "${BLUE}🗄️  初始化数据库表...${NC}"
        docker exec -i crawler_postgres psql -U stock_user -d stock_analysis << 'EOF'
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) UNIQUE NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market VARCHAR(20) NOT NULL,
    industry VARCHAR(50),
    capital_stock BIGINT,
    capital_updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_daily_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    volume BIGINT,
    turnover NUMERIC(15, 2),
    price_change NUMERIC(10, 2),
    price_change_rate NUMERIC(8, 4),
    ma5 NUMERIC(10, 2),
    ma10 NUMERIC(10, 2),
    ma20 NUMERIC(10, 2),
    data_source VARCHAR(50),
    data_quality VARCHAR(20),
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_stock_daily_code_date ON stock_daily_data(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_stock_daily_date ON stock_daily_data(trade_date);

INSERT INTO stocks (stock_code, stock_name, market, is_active) 
VALUES 
    ('2330', '台积电', 'TSE', true),
    ('2317', '鸿海', 'TSE', true),
    ('2454', '联发科', 'TSE', true),
    ('2882', '国泰金', 'TSE', true),
    ('2412', '中华电', 'TSE', true)
ON CONFLICT (stock_code) DO NOTHING;
EOF
        echo -e "${GREEN}✅ 数据库表初始化完成！${NC}"
        ;;
    8)
        echo -e "${BLUE}📥 爬取测试数据...${NC}"
        curl -X POST http://localhost:9627/api/v1/stocks/batch-update \
          -H "Content-Type: application/json" \
          -d '{"symbols": ["2330", "2317", "2454"]}'
        echo ""
        echo -e "${GREEN}✅ 爬取任务已提交！请稍后查看监控面板${NC}"
        ;;
    9)
        echo -e "${BLUE}🌐 打开监控面板...${NC}"
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:9627
        elif command -v explorer.exe > /dev/null; then
            explorer.exe http://localhost:9627
        else
            echo -e "${YELLOW}请在浏览器中打开: http://localhost:9627${NC}"
        fi
        ;;
    0)
        echo -e "${GREEN}👋 再见！${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================================${NC}"
