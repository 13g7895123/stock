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
// 使用與 Python 版本相同的兩步驟邏輯
// 步驟1: 智能分離日期和數字
// 步驟2: 根據日期數量動態切分數據
// 格式: date1,date2,...,dateN,open1,open2,...,openN,high1,...,highN,low1,...,lowN,close1,...,closeN,volume1,...,volumeN
func (p *Parser) ParseBrokerResponse(responseText, stockCode string) ([]DailyData, error) {
	if responseText == "" {
		return nil, fmt.Errorf("empty response")
	}

	// 分割原始資料
	parts := strings.Split(responseText, ",")
	if len(parts) == 0 {
		return nil, fmt.Errorf("invalid response format")
	}

	// 步驟 1: 智能分離日期和數字
	var dates []string
	var allNumbers []float64

	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		// 檢查是否為日期格式 (YYYY/MM/DD)
		if strings.Contains(part, "/") {
			dateParts := strings.Split(part, "/")
			if len(dateParts) == 3 {
				// 驗證是否為合法的西元年日期
				if year, err := strconv.Atoi(dateParts[0]); err == nil {
					if month, err := strconv.Atoi(dateParts[1]); err == nil {
						if day, err := strconv.Atoi(dateParts[2]); err == nil {
							// 西元年範圍驗證 (1900-2100)
							if year >= 1900 && year <= 2100 && month >= 1 && month <= 12 && day >= 1 && day <= 31 {
								dates = append(dates, part)
								continue
							}
						}
					}
				}
			}
		}

		// 嘗試解析為數字
		if num, err := strconv.ParseFloat(part, 64); err == nil {
			allNumbers = append(allNumbers, num)
		} else {
			// 處理混合格式 "date price" 或 "price1 price2"
			if strings.Contains(part, " ") {
				spaceParts := strings.Fields(part)
				for _, spacePart := range spaceParts {
					// 檢查是否為日期
					if strings.Contains(spacePart, "/") {
						dateParts := strings.Split(spacePart, "/")
						if len(dateParts) == 3 {
							if year, err := strconv.Atoi(dateParts[0]); err == nil {
								if year >= 1900 && year <= 2100 {
									dates = append(dates, spacePart)
									continue
								}
							}
						}
					}
					// 嘗試解析為數字
					if num, err := strconv.ParseFloat(spacePart, 64); err == nil {
						allNumbers = append(allNumbers, num)
					}
				}
			}
		}
	}

	if len(dates) == 0 {
		return nil, fmt.Errorf("no valid dates found in response")
	}

	if len(allNumbers) == 0 {
		return nil, fmt.Errorf("no valid numbers found in response")
	}

	// 步驟 2: 根據日期數量動態切分數據
	numDates := len(dates)

	// 驗證數據完整性（至少需要 OHLC 四個字段）
	if len(allNumbers) < numDates*4 {
		return nil, fmt.Errorf("insufficient data: need at least %d numbers for OHLC, got %d", numDates*4, len(allNumbers))
	}

	// 提取各部分數據
	opens := allNumbers[0:numDates]
	highs := allNumbers[numDates : numDates*2]
	lows := allNumbers[numDates*2 : numDates*3]
	closes := allNumbers[numDates*3 : numDates*4]

	// Volume 可能不存在，使用容錯處理
	var volumes []int64
	if len(allNumbers) >= numDates*5 {
		for i := 0; i < numDates; i++ {
			idx := numDates*4 + i
			if idx < len(allNumbers) {
				volumes = append(volumes, int64(allNumbers[idx]))
			} else {
				volumes = append(volumes, 0)
			}
		}
	} else {
		// 如果沒有 volume 數據，填充 0
		volumes = make([]int64, numDates)
	}

	// 組裝資料
	var result []DailyData

	for i := 0; i < numDates; i++ {
		// 解析日期（格式: 2025/09/01）
		tradeDate, err := p.parseDate(dates[i])
		if err != nil {
			continue // 跳過無效日期
		}

		// 驗證價格數據的有效性
		openPrice := opens[i]
		highPrice := highs[i]
		lowPrice := lows[i]
		closePrice := closes[i]
		volume := volumes[i]

		// 基本驗證：價格必須為正
		if openPrice <= 0 || highPrice <= 0 || lowPrice <= 0 || closePrice <= 0 || volume < 0 {
			continue
		}

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

	if len(result) == 0 {
		return nil, fmt.Errorf("no valid data parsed")
	}

	return result, nil
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
