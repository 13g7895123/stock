#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== 查看均線計算任務進度 ===${NC}"
echo ""

# 檢查服務是否運行
if ! curl -s http://localhost:9127/api/v1/health/ > /dev/null 2>&1; then
    echo -e "${RED}Backend API 未運行${NC}"
    exit 1
fi

# 查詢最新的均線計算任務
echo -e "${YELLOW}查詢進行中的任務...${NC}"

TASK_INFO=$(docker compose exec -T postgres psql -U stock_user -d stock_analysis -t -c "
SELECT id, task_name, status, progress, processed_count, total_count, success_count, error_count, result_summary
FROM task_execution_logs 
WHERE task_type = 'moving_averages_calculation' 
ORDER BY start_time DESC 
LIMIT 1;
")

if [ -z "$TASK_INFO" ]; then
    echo -e "${RED}找不到任何均線計算任務${NC}"
    exit 1
fi

# 解析任務資訊
TASK_ID=$(echo "$TASK_INFO" | awk -F'|' '{print $1}' | xargs)
TASK_NAME=$(echo "$TASK_INFO" | awk -F'|' '{print $2}' | xargs)
STATUS=$(echo "$TASK_INFO" | awk -F'|' '{print $3}' | xargs)
PROGRESS=$(echo "$TASK_INFO" | awk -F'|' '{print $4}' | xargs)
PROCESSED=$(echo "$TASK_INFO" | awk -F'|' '{print $5}' | xargs)
TOTAL=$(echo "$TASK_INFO" | awk -F'|' '{print $6}' | xargs)
SUCCESS=$(echo "$TASK_INFO" | awk -F'|' '{print $7}' | xargs)
ERRORS=$(echo "$TASK_INFO" | awk -F'|' '{print $8}' | xargs)
SUMMARY=$(echo "$TASK_INFO" | awk -F'|' '{print $9}' | xargs)

echo ""
echo -e "${CYAN}任務ID: ${TASK_ID}${NC}"
echo -e "任務名稱: ${TASK_NAME}"
echo -e "狀態: ${STATUS}"
echo ""

# 如果任務還在運行，持續監控
if [ "$STATUS" = "running" ]; then
    echo -e "${YELLOW}任務執行中，即時監控...${NC}"
    echo ""
    
    while true; do
        TASK_INFO=$(docker compose exec -T postgres psql -U stock_user -d stock_analysis -t -c "
        SELECT status, progress, processed_count, total_count, success_count, error_count, result_summary
        FROM task_execution_logs 
        WHERE id = $TASK_ID;
        ")
        
        STATUS=$(echo "$TASK_INFO" | awk -F'|' '{print $1}' | xargs)
        PROGRESS=$(echo "$TASK_INFO" | awk -F'|' '{print $2}' | xargs)
        PROCESSED=$(echo "$TASK_INFO" | awk -F'|' '{print $3}' | xargs)
        TOTAL=$(echo "$TASK_INFO" | awk -F'|' '{print $4}' | xargs)
        SUCCESS=$(echo "$TASK_INFO" | awk -F'|' '{print $5}' | xargs)
        ERRORS=$(echo "$TASK_INFO" | awk -F'|' '{print $6}' | xargs)
        SUMMARY=$(echo "$TASK_INFO" | awk -F'|' '{print $7}' | xargs)
        
        # 顯示進度條
        PROGRESS_INT=${PROGRESS%.*}
        PROGRESS_INT=${PROGRESS_INT:-0}
        FILLED=$((PROGRESS_INT / 5))
        PROGRESS_BAR=""
        for i in $(seq 1 20); do
            if [ $i -le $FILLED ]; then
                PROGRESS_BAR="${PROGRESS_BAR}█"
            else
                PROGRESS_BAR="${PROGRESS_BAR}░"
            fi
        done
        
        printf "\r${CYAN}[${PROGRESS_BAR}] ${PROGRESS}%% - ${PROCESSED}/${TOTAL} - 成功:${SUCCESS} 失敗:${ERRORS}${NC}          "
        
        if [ "$STATUS" = "completed" ]; then
            echo ""
            echo -e "${GREEN}任務完成！${NC}"
            echo -e "結果: ${SUMMARY}"
            break
        elif [ "$STATUS" = "failed" ]; then
            echo ""
            echo -e "${RED}任務失敗${NC}"
            echo -e "結果: ${SUMMARY}"
            break
        fi
        
        sleep 2
    done
else
    echo -e "進度: ${PROGRESS}%"
    echo -e "處理: ${PROCESSED}/${TOTAL}"
    echo -e "成功: ${SUCCESS}"
    echo -e "失敗: ${ERRORS}"
    echo -e "結果: ${SUMMARY}"
fi

echo ""
echo -e "${YELLOW}當前均線資料狀態:${NC}"
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
