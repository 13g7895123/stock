package scraper

import (
	"fmt"
)

// Validator 資料驗證器
type Validator struct{}

// NewValidator 建立驗證器
func NewValidator() *Validator {
	return &Validator{}
}

// Validate 驗證日線資料
func (v *Validator) Validate(data *DailyData) error {
	// 檢查必要欄位
	if data.StockCode == "" {
		return fmt.Errorf("stock_code is required")
	}

	if data.TradeDate.IsZero() {
		return fmt.Errorf("trade_date is required")
	}

	// 檢查價格邏輯
	if data.OpenPrice <= 0 {
		return fmt.Errorf("open_price must be positive")
	}

	if data.HighPrice <= 0 {
		return fmt.Errorf("high_price must be positive")
	}

	if data.LowPrice <= 0 {
		return fmt.Errorf("low_price must be positive")
	}

	if data.ClosePrice <= 0 {
		return fmt.Errorf("close_price must be positive")
	}

	// 檢查價格關係
	// 最高價必須 >= 開盤價、收盤價、最低價
	if data.HighPrice < data.OpenPrice {
		return fmt.Errorf("high_price must be >= open_price")
	}

	if data.HighPrice < data.ClosePrice {
		return fmt.Errorf("high_price must be >= close_price")
	}

	if data.HighPrice < data.LowPrice {
		return fmt.Errorf("high_price must be >= low_price")
	}

	// 最低價必須 <= 開盤價、收盤價
	if data.LowPrice > data.OpenPrice {
		return fmt.Errorf("low_price must be <= open_price")
	}

	if data.LowPrice > data.ClosePrice {
		return fmt.Errorf("low_price must be <= close_price")
	}

	// 檢查成交量
	if data.Volume < 0 {
		return fmt.Errorf("volume cannot be negative")
	}

	return nil
}

// ValidateBatch 批次驗證
func (v *Validator) ValidateBatch(dataList []DailyData) ([]DailyData, []error) {
	var validData []DailyData
	var errors []error

	for i, data := range dataList {
		if err := v.Validate(&data); err != nil {
			errors = append(errors, fmt.Errorf("record %d: %w", i, err))
		} else {
			validData = append(validData, data)
		}
	}

	return validData, errors
}

// IsDataComplete 檢查資料是否完整
func (v *Validator) IsDataComplete(data *DailyData) bool {
	return data.StockCode != "" &&
		!data.TradeDate.IsZero() &&
		data.OpenPrice > 0 &&
		data.HighPrice > 0 &&
		data.LowPrice > 0 &&
		data.ClosePrice > 0
}

// SanitizeData 清理資料（移除異常值）
func (v *Validator) SanitizeData(data []DailyData) []DailyData {
	var result []DailyData

	for _, d := range data {
		// 檢查價格是否合理（例如：不能超過 10 倍差距）
		if d.HighPrice > d.LowPrice*10 {
			continue // 跳過異常資料
		}

		// 檢查日期是否合理
		if d.TradeDate.Year() < 1990 || d.TradeDate.Year() > 2100 {
			continue
		}

		result = append(result, d)
	}

	return result
}
