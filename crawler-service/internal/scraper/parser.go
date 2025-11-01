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
// 格式: dates,dates,...,opens,opens,...,highs,highs,...,lows,lows,...,closes,closes,...,volumes,volumes,...
func (p *Parser) ParseBrokerResponse(responseText, stockCode string) ([]DailyData, error) {
	if responseText == "" {
		return nil, fmt.Errorf("empty response")
	}

	// 分離不同類型的資料
	parts := strings.Split(responseText, ",")
	if len(parts) == 0 {
		return nil, fmt.Errorf("invalid response format")
	}

	// 計算每個部分的長度
	// 假設格式: dates, opens, highs, lows, closes, volumes (6 個部分)
	totalParts := len(parts)
	if totalParts%6 != 0 {
		return nil, fmt.Errorf("invalid data format: parts count %d is not divisible by 6", totalParts)
	}

	recordCount := totalParts / 6

	// 提取各部分
	dates := parts[0:recordCount]
	opens := parts[recordCount : recordCount*2]
	highs := parts[recordCount*2 : recordCount*3]
	lows := parts[recordCount*3 : recordCount*4]
	closes := parts[recordCount*4 : recordCount*5]
	volumes := parts[recordCount*5 : recordCount*6]

	// 組裝資料
	var result []DailyData

	for i := 0; i < recordCount; i++ {
		// 解析日期（格式: 106/05/02 → 2017-05-02）
		tradeDate, err := p.parseROCDate(dates[i])
		if err != nil {
			continue // 跳過無效日期
		}

		// 解析價格和成交量
		openPrice, err := strconv.ParseFloat(opens[i], 64)
		if err != nil {
			continue
		}

		highPrice, err := strconv.ParseFloat(highs[i], 64)
		if err != nil {
			continue
		}

		lowPrice, err := strconv.ParseFloat(lows[i], 64)
		if err != nil {
			continue
		}

		closePrice, err := strconv.ParseFloat(closes[i], 64)
		if err != nil {
			continue
		}

		volume, err := strconv.ParseInt(volumes[i], 10, 64)
		if err != nil {
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
