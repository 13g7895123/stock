#!/bin/bash
# 批量填補缺失的均線資料腳本
# 這個腳本使用 SQL 視窗函數高效計算缺失的均線

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DB_CONTAINER="stock_postgres"
DB_USER="stock_user"
DB_NAME="stock_analysis"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}      批量填補缺失均線資料工具${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. 先插入缺失的記錄
echo -e "${BLUE}📊 步驟 1: 檢查並插入缺失的均線記錄...${NC}"
MISSING=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -A -c "
SELECT COUNT(*) FROM stock_daily_data sdd
WHERE NOT EXISTS (
    SELECT 1 FROM moving_averages ma 
    WHERE ma.stock_id = sdd.stock_code 
    AND ma.trade_date = sdd.trade_date
);")
echo -e "   缺失記錄數: ${YELLOW}$MISSING${NC}"

if [ "$MISSING" -gt 0 ]; then
    echo -e "${YELLOW}   插入缺失的記錄...${NC}"
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
    INSERT INTO moving_averages (stock_id, trade_date, ma_5, ma_10, ma_20, ma_60, ma_72, ma_120, ma_240)
    SELECT sdd.stock_code, sdd.trade_date, NULL, NULL, NULL, NULL, NULL, NULL, NULL
    FROM stock_daily_data sdd
    WHERE NOT EXISTS (
        SELECT 1 FROM moving_averages ma 
        WHERE ma.stock_id = sdd.stock_code 
        AND ma.trade_date = sdd.trade_date
    )
    ON CONFLICT DO NOTHING;
    "
    echo -e "${GREEN}   ✅ 插入完成${NC}"
fi

# 2. 分批更新均線
echo ""
echo -e "${BLUE}📊 步驟 2: 批量計算均線值...${NC}"

# 取得所有有缺失均線的股票清單
STOCKS=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -A -c "
SELECT DISTINCT stock_id FROM moving_averages 
WHERE ma_5 IS NULL OR ma_10 IS NULL OR ma_20 IS NULL 
   OR ma_60 IS NULL OR ma_72 IS NULL OR ma_120 IS NULL OR ma_240 IS NULL
ORDER BY stock_id;
")

STOCK_COUNT=$(echo "$STOCKS" | wc -l)
echo -e "   需要處理的股票數: ${YELLOW}$STOCK_COUNT${NC}"

if [ "$STOCK_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ 所有均線資料都已完整！${NC}"
    exit 0
fi

# 批量處理，每次處理 50 支股票
BATCH_SIZE=50
CURRENT=0
BATCH_NUM=0

# 將股票列表分割成批次
echo "$STOCKS" | while IFS= read -r STOCK_ID; do
    if [ -z "$STOCK_ID" ]; then
        continue
    fi
    
    CURRENT=$((CURRENT + 1))
    PERCENT=$((CURRENT * 100 / STOCK_COUNT))
    
    # 每 10 支股票顯示一次進度
    if [ $((CURRENT % 10)) -eq 0 ] || [ "$CURRENT" -eq "$STOCK_COUNT" ]; then
        echo -ne "\r${GREEN}⏳ 進度: ${YELLOW}$CURRENT${GREEN}/${YELLOW}$STOCK_COUNT${GREEN} (${PERCENT}%)${NC}          "
    fi
    
    # 更新單一股票的所有均線
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -q -c "
    WITH ranked_data AS (
        SELECT 
            sdd.stock_code,
            sdd.trade_date,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as calc_ma5,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as calc_ma10,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as calc_ma20,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) as calc_ma60,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 71 PRECEDING AND CURRENT ROW) as calc_ma72,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 119 PRECEDING AND CURRENT ROW) as calc_ma120,
            AVG(sdd.close_price) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 239 PRECEDING AND CURRENT ROW) as calc_ma240,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as cnt_5,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as cnt_10,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as cnt_20,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) as cnt_60,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 71 PRECEDING AND CURRENT ROW) as cnt_72,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 119 PRECEDING AND CURRENT ROW) as cnt_120,
            COUNT(*) OVER (PARTITION BY sdd.stock_code ORDER BY sdd.trade_date ROWS BETWEEN 239 PRECEDING AND CURRENT ROW) as cnt_240
        FROM stock_daily_data sdd
        WHERE sdd.stock_code = '$STOCK_ID'
    )
    UPDATE moving_averages ma
    SET 
        ma_5 = CASE WHEN rd.cnt_5 >= 5 THEN ROUND(rd.calc_ma5::numeric, 2) ELSE ma.ma_5 END,
        ma_10 = CASE WHEN rd.cnt_10 >= 10 THEN ROUND(rd.calc_ma10::numeric, 2) ELSE ma.ma_10 END,
        ma_20 = CASE WHEN rd.cnt_20 >= 20 THEN ROUND(rd.calc_ma20::numeric, 2) ELSE ma.ma_20 END,
        ma_60 = CASE WHEN rd.cnt_60 >= 60 THEN ROUND(rd.calc_ma60::numeric, 2) ELSE ma.ma_60 END,
        ma_72 = CASE WHEN rd.cnt_72 >= 72 THEN ROUND(rd.calc_ma72::numeric, 2) ELSE ma.ma_72 END,
        ma_120 = CASE WHEN rd.cnt_120 >= 120 THEN ROUND(rd.calc_ma120::numeric, 2) ELSE ma.ma_120 END,
        ma_240 = CASE WHEN rd.cnt_240 >= 240 THEN ROUND(rd.calc_ma240::numeric, 2) ELSE ma.ma_240 END
    FROM ranked_data rd
    WHERE ma.stock_id = rd.stock_code 
      AND ma.trade_date = rd.trade_date;
    " 2>/dev/null
done

echo ""
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 均線填補完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 最終統計
echo ""
echo -e "${BLUE}📊 最終統計:${NC}"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    COUNT(*) as \"總記錄數\",
    COUNT(ma_5) as \"有MA5\",
    COUNT(ma_10) as \"有MA10\",
    COUNT(ma_20) as \"有MA20\",
    COUNT(ma_60) as \"有MA60\",
    COUNT(ma_72) as \"有MA72\",
    COUNT(ma_120) as \"有MA120\",
    COUNT(ma_240) as \"有MA240\"
FROM moving_averages;
"

# 顯示 2025-11-28 的股票數
echo ""
echo -e "${BLUE}📈 2025-11-28 的股票均線統計:${NC}"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT COUNT(DISTINCT stock_id) as \"有均線的股票數\"
FROM moving_averages
WHERE trade_date::date = '2025-11-28' AND ma_5 IS NOT NULL;
"
