package scraper

import (
"fmt"
"strconv"
"strings"
"time"
)

// Parser 資料解析器
type Parser struct{}

// NewParser 建立解析器
func NewParser() *Parser {
return &Parser{}
}

// cleanValue 清理數值字串（移除逗號、貨幣符號、空白）
func cleanValue(value string) string {
value = strings.ReplaceAll(value, ",", "")
value = strings.ReplaceAll(value, "$", "")
value = strings.ReplaceAll(value, "元", "")
value = strings.ReplaceAll(value, "TWD", "")
value = strings.TrimSpace(value)
return value
}

// parseFloat 解析浮點數
func parseFloat(value string) (float64, error) {
value = cleanValue(value)
if value == "" || value == "-" || value == "N/A" {
return 0, fmt.Errorf("empty value")
}
return strconv.ParseFloat(value, 64)
}

// parseInt 解析整數
func parseInt(value string) (int64, error) {
value = cleanValue(value)
if value == "" || value == "-" || value == "N/A" {
return 0, fmt.Errorf("empty value")
}
return strconv.ParseInt(value, 10, 64)
}

// ParseBrokerResponse 解析券商回應
// 完全匹配 Python 版本的解析邏輯
// 格式: "日期1,日期2,...,日期N 開盤1,開盤2,...,開盤N 最高1,最高2,...,最高N 最低1,最低2,...,最低N 收盤1,收盤2,...,收盤N 成交量1,成交量2,...,成交量N"
// 步驟1: 先用空白分隔不同類型的資料（日期、開盤、最高、最低、收盤、成交量）
// 步驟2: 每個類型內部用逗號分隔
func (p *Parser) ParseBrokerResponse(responseText, stockCode string) ([]DailyData, error) {
if responseText == "" {
return nil, fmt.Errorf("empty response")
}

// 步驟 1: 用空白分隔不同類型的資料陣列
sections := strings.Fields(responseText)
if len(sections) < 5 {
return nil, fmt.Errorf("invalid response format: expected at least 5 sections (date, open, high, low, close), got %d", len(sections))
}

// 步驟 2: 解析每個區段
// sections[0] = 日期陣列 (date1,date2,...)
// sections[1] = 開盤價陣列 (open1,open2,...)
// sections[2] = 最高價陣列 (high1,high2,...)
// sections[3] = 最低價陣列 (low1,low2,...)
// sections[4] = 收盤價陣列 (close1,close2,...)
// sections[5] = 成交量陣列 (vol1,vol2,...) 可能不存在

dates := strings.Split(sections[0], ",")
opens := strings.Split(sections[1], ",")
highs := strings.Split(sections[2], ",")
lows := strings.Split(sections[3], ",")
closes := strings.Split(sections[4], ",")

var volumes []string
if len(sections) >= 6 {
volumes = strings.Split(sections[5], ",")
}

// 驗證各陣列長度一致
numRecords := len(dates)
if len(opens) != numRecords || len(highs) != numRecords || len(lows) != numRecords || len(closes) != numRecords {
return nil, fmt.Errorf("inconsistent data length: dates=%d, opens=%d, highs=%d, lows=%d, closes=%d",
len(dates), len(opens), len(highs), len(lows), len(closes))
}

// 步驟 3: 逐筆組裝資料
var result []DailyData

for i := 0; i < numRecords; i++ {
// 解析日期
dateStr := strings.TrimSpace(dates[i])
if dateStr == "" {
continue
}

tradeDate, err := p.parseDate(dateStr)
if err != nil {
continue // 跳過無效日期
}

// 解析價格
openPrice, err := parseFloat(opens[i])
if err != nil {
continue
}

highPrice, err := parseFloat(highs[i])
if err != nil {
continue
}

lowPrice, err := parseFloat(lows[i])
if err != nil {
continue
}

closePrice, err := parseFloat(closes[i])
if err != nil {
continue
}

// 解析成交量（可能不存在）
var volume int64
if i < len(volumes) {
if vol, err := parseInt(volumes[i]); err == nil {
volume = vol
}
}

// 基本驗證：價格必須為正，且最低價 <= 最高價
if openPrice > 0 && highPrice > 0 && lowPrice > 0 && closePrice > 0 && volume >= 0 {
if lowPrice <= highPrice {
data := DailyData{
StockCode:   stockCode,
TradeDate:   tradeDate,
OpenPrice:   openPrice,
HighPrice:   highPrice,
LowPrice:    lowPrice,
ClosePrice:  closePrice,
Volume:      volume,
DataSource:  "go_broker_crawler",
DataQuality: "corrected_daily",
}

result = append(result, data)
}
}
}

if len(result) == 0 {
return nil, fmt.Errorf("no valid data parsed")
}

return result, nil
}

// parseDate 解析日期（支援西元年格式: YYYY/MM/DD）
func (p *Parser) parseDate(dateStr string) (time.Time, error) {
parts := strings.Split(dateStr, "/")
if len(parts) != 3 {
return time.Time{}, fmt.Errorf("invalid date format: %s", dateStr)
}

year, err := strconv.Atoi(parts[0])
if err != nil {
return time.Time{}, fmt.Errorf("invalid year: %s", parts[0])
}

month, err := strconv.Atoi(parts[1])
if err != nil {
return time.Time{}, fmt.Errorf("invalid month: %s", parts[1])
}

day, err := strconv.Atoi(parts[2])
if err != nil {
return time.Time{}, fmt.Errorf("invalid day: %s", parts[2])
}

// 驗證日期合法性
if year < 1900 || year > 2100 || month < 1 || month > 12 || day < 1 || day > 31 {
return time.Time{}, fmt.Errorf("invalid date values: %s", dateStr)
}

return time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.Local), nil
}

// parseROCDate 解析民國日期
// 格式: 106/05/02 → 2017-05-02
func (p *Parser) parseROCDate(rocDate string) (time.Time, error) {
parts := strings.Split(rocDate, "/")
if len(parts) != 3 {
return time.Time{}, fmt.Errorf("invalid date format: %s", rocDate)
}

// 民國年 + 1911 = 西元年
year, err := strconv.Atoi(parts[0])
if err != nil {
return time.Time{}, err
}
year += 1911

month, err := strconv.Atoi(parts[1])
if err != nil {
return time.Time{}, err
}

day, err := strconv.Atoi(parts[2])
if err != nil {
return time.Time{}, err
}

return time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.Local), nil
}

// ParseTabDelimited 解析 tab 分隔格式（備用解析器）
func (p *Parser) ParseTabDelimited(responseText, stockCode string) ([]DailyData, error) {
lines := strings.Split(responseText, "\n")
var result []DailyData

for _, line := range lines {
line = strings.TrimSpace(line)
if line == "" {
continue
}

parts := strings.Split(line, "\t")
if len(parts) < 6 {
continue
}

// 解析日期
tradeDate, err := p.parseROCDate(parts[0])
if err != nil {
continue
}

// 解析數值
openPrice, _ := strconv.ParseFloat(parts[1], 64)
highPrice, _ := strconv.ParseFloat(parts[2], 64)
lowPrice, _ := strconv.ParseFloat(parts[3], 64)
closePrice, _ := strconv.ParseFloat(parts[4], 64)
volume, _ := strconv.ParseInt(parts[5], 10, 64)

data := DailyData{
StockCode:   stockCode,
TradeDate:   tradeDate,
OpenPrice:   openPrice,
HighPrice:   highPrice,
LowPrice:    lowPrice,
ClosePrice:  closePrice,
Volume:      volume,
DataSource:  "go_broker_crawler",
DataQuality: "corrected_daily",
}

result = append(result, data)
}

return result, nil
}
