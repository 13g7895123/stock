#!/bin/bash
# 高效批量更新均線資料腳本
# 此腳本直接使用 SQL 進行批量計算，效率更高

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 取得容器名稱和資料庫設定
BACKEND_CONTAINER="stock_backend"
DB_CONTAINER="stock_postgres"
DB_USER="stock_user"
DB_NAME="stock_analysis"

if [ -z "$DB_CONTAINER" ]; then
    echo -e "${RED}❌ 找不到資料庫容器${NC}"
    exit 1
fi

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}      高效批量均線更新工具${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 統計目前狀況
echo -e "${BLUE}📊 正在統計資料狀況...${NC}"
STATS=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -A -c "
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN ma_20 IS NULL THEN 1 END) as need_ma20,
    COUNT(CASE WHEN ma_72 IS NULL THEN 1 END) as need_ma72,
    COUNT(CASE WHEN ma_120 IS NULL THEN 1 END) as need_ma120,
    COUNT(CASE WHEN ma_240 IS NULL THEN 1 END) as need_ma240
FROM moving_averages;
")

IFS='|' read -r TOTAL NEED_MA20 NEED_MA72 NEED_MA120 NEED_MA240 <<< "$STATS"

echo -e "${GREEN}📈 資料統計:${NC}"
echo -e "   總記錄數: ${YELLOW}$TOTAL${NC}"
echo -e "   需更新 MA20: ${YELLOW}$NEED_MA20${NC}"
echo -e "   需更新 MA72: ${YELLOW}$NEED_MA72${NC}"
echo -e "   需更新 MA120: ${YELLOW}$NEED_MA120${NC}"
echo -e "   需更新 MA240: ${YELLOW}$NEED_MA240${NC}"
echo ""

# 取得股票列表
STOCKS=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -A -c "
SELECT DISTINCT stock_id FROM moving_averages ORDER BY stock_id;
")

STOCK_COUNT=$(echo "$STOCKS" | wc -l)
echo -e "${BLUE}🏢 共有 ${YELLOW}$STOCK_COUNT${BLUE} 支股票需要處理${NC}"
echo ""

# 計算每支股票的均線
CURRENT=0
for STOCK_ID in $STOCKS; do
    CURRENT=$((CURRENT + 1))
    
    # 顯示進度
    PERCENT=$((CURRENT * 100 / STOCK_COUNT))
    echo -ne "\r${GREEN}⏳ 進度: ${YELLOW}$CURRENT${GREEN}/${YELLOW}$STOCK_COUNT${GREEN} (${PERCENT}%) - 處理股票: ${CYAN}$STOCK_ID${NC}          "
    
    # 使用 SQL 視窗函數計算均線並更新
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -q -c "
    WITH ranked_data AS (
        SELECT 
            sdd.id as data_id,
            sdd.stock_code,
            sdd.trade_date,
            sdd.close_price,
            AVG(sdd.close_price) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as calc_ma20,
            AVG(sdd.close_price) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 71 PRECEDING AND CURRENT ROW
            ) as calc_ma72,
            AVG(sdd.close_price) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
            ) as calc_ma120,
            AVG(sdd.close_price) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 239 PRECEDING AND CURRENT ROW
            ) as calc_ma240,
            COUNT(*) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as cnt_20,
            COUNT(*) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 71 PRECEDING AND CURRENT ROW
            ) as cnt_72,
            COUNT(*) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 119 PRECEDING AND CURRENT ROW
            ) as cnt_120,
            COUNT(*) OVER (
                PARTITION BY sdd.stock_code 
                ORDER BY sdd.trade_date 
                ROWS BETWEEN 239 PRECEDING AND CURRENT ROW
            ) as cnt_240
        FROM stock_daily_data sdd
        WHERE sdd.stock_code = '$STOCK_ID'
    )
    UPDATE moving_averages ma
    SET 
        ma_20 = CASE WHEN rd.cnt_20 >= 20 THEN ROUND(rd.calc_ma20::numeric, 2) ELSE ma.ma_20 END,
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
echo -e "${GREEN}✅ 均線更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 最終統計
echo -e "${BLUE}📊 最終統計:${NC}"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    COUNT(*) as \"總記錄數\",
    COUNT(ma_5) as \"有MA5\",
    COUNT(ma_10) as \"有MA10\",
    COUNT(ma_20) as \"有MA20\",
    COUNT(ma_72) as \"有MA72\",
    COUNT(ma_120) as \"有MA120\",
    COUNT(ma_240) as \"有MA240\"
FROM moving_averages;
"
