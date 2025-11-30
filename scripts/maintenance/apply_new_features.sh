#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 開始套用新功能更新 ===${NC}"

# 1. 停止現有服務
echo -e "${YELLOW}1. 停止現有服務...${NC}"
docker compose down

# 2. 清理舊的容器和暫存（選擇性，確保乾淨的環境）
# echo -e "${YELLOW}2. 清理舊容器...${NC}"
# docker system prune -f

# 3. 重新建置並啟動服務
echo -e "${YELLOW}3. 重新建置並啟動服務 (Backend & Frontend)...${NC}"
# 我們特別指定重建 backend 和 frontend，因為這兩個服務有程式碼變更
docker compose up -d --build backend frontend

# 4. 啟動其他服務
echo -e "${YELLOW}4. 啟動其餘服務...${NC}"
docker compose up -d

# 5. 等待服務就緒
echo -e "${YELLOW}5. 等待服務啟動...${NC}"
echo "等待 10 秒讓服務初始化..."
sleep 10

# 6. 檢查服務狀態
echo -e "${YELLOW}6. 檢查服務狀態...${NC}"
if curl -s http://localhost:8000/api/v1/health/ > /dev/null; then
    echo -e "${GREEN}Backend API 運作正常${NC}"
else
    echo -e "${RED}Backend API 似乎未正常回應，請檢查 logs${NC}"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}Frontend 運作正常${NC}"
else
    echo -e "${RED}Frontend 似乎未正常回應，請檢查 logs${NC}"
fi

echo -e "${GREEN}=== 更新完成 ===${NC}"
echo -e "您可以訪問以下網址使用新功能："
echo -e "1. 歷史資料管理 (Dashboard): http://localhost:3000/dashboard/overview"
echo -e "2. 智能選股 - 所有股票 (Stock Selection): http://localhost:3000/market-data/stock-selection"
