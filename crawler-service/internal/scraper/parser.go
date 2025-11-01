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

// ParseBrokerResponse 解析券商回應
// 完全匹配 Python 版本的解析邏輯
// 格式: date1,date2,...,dateN,data1_1,data1_2,...data1_5,data2_1,...
// 其中每個日期對應 5 個數據點: open, high, low, close, volume
func (p *Parser) ParseBrokerResponse(responseText, stockCode string) ([]DailyData, error) {
	if responseText == "" {
		return nil, fmt.Errorf("empty response")
	}

	// 分割原始資料
	parts := strings.Split(responseText, ",")
	if len(parts) == 0 {
		return nil, fmt.Errorf("invalid response format")
	}

	// 步驟 1: 分離日期和數字（完全匹配 Python 邏輯）
	var dates []string
	var numbers []float64

	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		// 檢查是否為日期格式 (YYYY/MM/DD)
		if strings.Contains(part, "/") && len(strings.Split(part, "/")) == 3 {
			dates = append(dates, part)
		} else {
			// 嘗試解析為數字
			if num, err := strconv.ParseFloat(part, 64); err == nil {
				numbers = append(numbers, num)
			}
			// 非數字且非日期的部分會被跳過
		}
	}

	if len(dates) == 0 {
		return nil, fmt.Errorf("no valid dates found in response")
	}

	if len(numbers) == 0 {
		return nil, fmt.Errorf("no valid numbers found in response")
	}

	// 步驟 2: 計算每個日期對應的數據點數量（Python 邏輯）
	dataPointsPerDate := len(numbers) / len(dates)
	
	if dataPointsPerDate < 4 {
		return nil, fmt.Errorf("not enough data points per date: need at least 4 (OHLC), got %d", dataPointsPerDate)
	}

	// 步驟 3: 逐日期解析資料
	var result []DailyData

	for i, dateStr := range dates {
		// 解析日期
		tradeDate, err := p.parseDate(dateStr)
		if err != nil {
			continue // 跳過無效日期
		}

		// 計算此日期對應的數據索引
		startIdx := i * dataPointsPerDate
		endIdx := startIdx + dataPointsPerDate

		if endIdx > len(numbers) {
			continue // 數據不完整，跳過
		}

		dataPoints := numbers[startIdx:endIdx]

		// 檢查是否有足夠的數據點
		if len(dataPoints) < 5 {
			continue
		}

		// 解析 OHLCV（假設順序為：open, high, low, close, volume）
		openPrice := dataPoints[0]
		highPrice := dataPoints[1]
		lowPrice := dataPoints[2]
		closePrice := dataPoints[3]
		volume := int64(dataPoints[4])

		// 基本驗證（完全匹配 Python 的驗證邏輯）
		if openPrice > 0 && highPrice > 0 && lowPrice > 0 && closePrice > 0 && volume >= 0 &&
			lowPrice <= openPrice && openPrice <= highPrice &&
			lowPrice <= closePrice && closePrice <= highPrice {

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
