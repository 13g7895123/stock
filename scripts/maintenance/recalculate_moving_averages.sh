#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== 重新計算缺失的均線資料（非同步多工版本）===${NC}"
echo ""

# 檢查服務是否運行
echo -e "${YELLOW}1. 檢查服務狀態...${NC}"
if ! curl -s http://localhost:9127/api/v1/health/ > /dev/null 2>&1; then
    echo -e "${RED}Backend API 未運行，請先啟動服務${NC}"
    exit 1
fi
echo -e "${GREEN}服務運行中${NC}"

# 顯示當前狀態
echo ""
echo -e "${YELLOW}2. 當前均線資料狀態:${NC}"
docker compose exec -T postgres psql -U stock_user -d stock_analysis -c "
SELECT 
    COUNT(*) as total_records,
    COUNT(ma_5) as has_ma5,
    COUNT(ma_10) as has_ma10,
    COUNT(ma_20) as has_ma20,
    COUNT(ma_60) as has_ma60,
    COUNT(ma_120) as has_ma120,
    COUNT(ma_240) as has_ma240
FROM moving_averages;
"

echo ""
echo -e "${YELLOW}3. 啟動非同步多工均線計算任務...${NC}"

# 呼叫非同步 API 啟動計算任務
RESPONSE=$(curl -s -X POST "http://localhost:9127/api/v1/moving-averages/calculate-async" \
    -H "Content-Type: application/json" \
    -d '{
        "stock_codes": null,
        "periods": [5, 10, 20, 60, 120, 240],
        "force_recalculate": false,
        "batch_size": 50
    }')

TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('task_id', ''))" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
    echo -e "${RED}啟動任務失敗:${NC}"
    echo "$RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
    exit 1
fi

echo -e "${GREEN}任務已啟動，Task ID: ${TASK_ID}${NC}"

# 輪詢任務狀態
echo ""
echo -e "${YELLOW}4. 等待任務完成（多線程並行處理中）...${NC}"

while true; do
    STATUS_RESPONSE=$(curl -s "http://localhost:9127/api/v1/moving-averages/task-status/${TASK_ID}")
    
    STATE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('state', 'UNKNOWN'))" 2>/dev/null)
    CURRENT=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('current', 0))" 2>/dev/null)
    TOTAL=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('total', 0))" 2>/dev/null)
    PERCENTAGE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('percentage', 0))" 2>/dev/null)
    STAGE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('stage', ''))" 2>/dev/null)
    
    # 顯示進度條
    PROGRESS_BAR=""
    FILLED=$((PERCENTAGE / 5))
    for i in $(seq 1 20); do
        if [ $i -le $FILLED ]; then
            PROGRESS_BAR="${PROGRESS_BAR}█"
        else
            PROGRESS_BAR="${PROGRESS_BAR}░"
        fi
    done
    
    printf "\r${CYAN}[${PROGRESS_BAR}] ${PERCENTAGE}%% - ${CURRENT}/${TOTAL} - ${STAGE}${NC}          "
    
    if [ "$STATE" = "SUCCESS" ]; then
        echo ""
        echo -e "${GREEN}任務完成！${NC}"
        echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); result = data.get('data', {}).get('result', {}); print(f\"成功: {result.get('processed_stocks', 0)} 檔，失敗: {result.get('failed_stocks', 0)} 檔，總計算量: {result.get('total_calculations', 0)} 筆\")"
        break
    elif [ "$STATE" = "FAILURE" ]; then
        echo ""
        echo -e "${RED}任務失敗${NC}"
        echo "$STATUS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('error', '未知錯誤'))"
        exit 1
    fi
    
    sleep 2
done

echo ""
echo -e "${YELLOW}5. 計算完成後的均線資料狀態:${NC}"
docker compose exec -T postgres psql -U stock_user -d stock_analysis -c "
SELECT 
    COUNT(*) as total_records,
    COUNT(ma_5) as has_ma5,
    COUNT(ma_10) as has_ma10,
    COUNT(ma_20) as has_ma20,
    COUNT(ma_60) as has_ma60,
    COUNT(ma_120) as has_ma120,
    COUNT(ma_240) as has_ma240
FROM moving_averages;
"

echo ""
echo -e "${GREEN}=== 均線重新計算完成 ===${NC}"
