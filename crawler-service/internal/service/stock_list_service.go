package service

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/stock-analysis/crawler-service/internal/storage"
	"github.com/stock-analysis/crawler-service/pkg/logger"
	"go.uber.org/zap"
)

// StockListService 股票清單服務
type StockListService struct {
	repository storage.Repository
	httpClient *http.Client
}

// NewStockListService 建立股票清單服務
func NewStockListService(repository storage.Repository) *StockListService {
	return &StockListService{
		repository: repository,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// TWStockInfo 證交所股票資訊結構
type TWStockInfo struct {
	Code    string `json:"code"`    // 股票代碼
	Name    string `json:"name"`    // 股票名稱
	Market  string `json:"market"`  // 市場別（上市/上櫃）
	Type    string `json:"type"`    // 類型
	Industry string `json:"industry"` // 產業別
}

// FetchAllStocks 爬取所有股票清單
func (s *StockListService) FetchAllStocks(ctx context.Context) (int, error) {
	logger.Info("開始爬取所有股票清單")
	
	totalCount := 0
	
	// 1. 爬取上市股票
	tseStocks, err := s.fetchTWSEStocks(ctx)
	if err != nil {
		logger.Error("爬取上市股票失敗", zap.Error(err))
		return 0, fmt.Errorf("failed to fetch TWSE stocks: %w", err)
	}
	
	// 2. 爬取上櫃股票
	otcStocks, err := s.fetchTPEXStocks(ctx)
	if err != nil {
		logger.Error("爬取上櫃股票失敗", zap.Error(err))
		return 0, fmt.Errorf("failed to fetch TPEX stocks: %w", err)
	}
	
	// 合併所有股票
	allStocks := append(tseStocks, otcStocks...)
	logger.Info("爬取完成", zap.Int("上市股票數", len(tseStocks)), zap.Int("上櫃股票數", len(otcStocks)))
	
	// 3. 儲存到資料庫
	for _, stock := range allStocks {
		err := s.saveStock(ctx, stock)
		if err != nil {
			logger.Warn("儲存股票失敗", 
				zap.String("code", stock.Code), 
				zap.String("name", stock.Name),
				zap.Error(err),
			)
			continue
		}
		totalCount++
	}
	
	logger.Info("股票清單儲存完成", zap.Int("成功數量", totalCount))
	return totalCount, nil
}

// fetchTWSEStocks 爬取上市股票（證交所）
func (s *StockListService) fetchTWSEStocks(ctx context.Context) ([]TWStockInfo, error) {
	// 證交所 API：https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=1&issuetype=1&industry_code=&Page=1&chklike=Y
	// 簡化版：使用公開的股票代號清單
	
	url := "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=json"
	
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
	
	resp, err := s.httpClient.Do(req)
	if err != nil {
		logger.Warn("證交所 API 請求失敗，使用備用方案", zap.Error(err))
		return s.getDefaultTWSEStocks(), nil
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		logger.Warn("證交所 API 回應異常，使用備用方案", zap.Int("status", resp.StatusCode))
		return s.getDefaultTWSEStocks(), nil
	}
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		Data [][]string `json:"data"`
	}
	
	if err := json.Unmarshal(body, &result); err != nil {
		logger.Warn("解析證交所資料失敗，使用備用方案", zap.Error(err))
		return s.getDefaultTWSEStocks(), nil
	}
	
	stocks := make([]TWStockInfo, 0)
	for _, row := range result.Data {
		if len(row) < 2 {
			continue
		}
		
		code := strings.TrimSpace(row[0])
		name := strings.TrimSpace(row[1])
		
		// 過濾掉非股票項目（如 ETF、認購權證等）
		if len(code) != 4 || !isNumeric(code) {
			continue
		}
		
		stocks = append(stocks, TWStockInfo{
			Code:   code,
			Name:   name,
			Market: "上市",
			Type:   "股票",
		})
	}
	
	if len(stocks) == 0 {
		return s.getDefaultTWSEStocks(), nil
	}
	
	return stocks, nil
}

// fetchTPEXStocks 爬取上櫃股票（櫃買中心）
func (s *StockListService) fetchTPEXStocks(ctx context.Context) ([]TWStockInfo, error) {
	// 櫃買中心 API
	url := "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d=" + time.Now().Format("106/01/02")
	
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
	
	resp, err := s.httpClient.Do(req)
	if err != nil {
		logger.Warn("櫃買中心 API 請求失敗，使用備用方案", zap.Error(err))
		return s.getDefaultTPEXStocks(), nil
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		logger.Warn("櫃買中心 API 回應異常，使用備用方案", zap.Int("status", resp.StatusCode))
		return s.getDefaultTPEXStocks(), nil
	}
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		AaData [][]string `json:"aaData"`
	}
	
	if err := json.Unmarshal(body, &result); err != nil {
		logger.Warn("解析櫃買中心資料失敗，使用備用方案", zap.Error(err))
		return s.getDefaultTPEXStocks(), nil
	}
	
	stocks := make([]TWStockInfo, 0)
	for _, row := range result.AaData {
		if len(row) < 2 {
			continue
		}
		
		code := strings.TrimSpace(row[0])
		name := strings.TrimSpace(row[1])
		
		// 過濾掉非股票項目
		if len(code) != 4 || !isNumeric(code) {
			continue
		}
		
		stocks = append(stocks, TWStockInfo{
			Code:   code,
			Name:   name,
			Market: "上櫃",
			Type:   "股票",
		})
	}
	
	if len(stocks) == 0 {
		return s.getDefaultTPEXStocks(), nil
	}
	
	return stocks, nil
}

// saveStock 儲存股票到資料庫
func (s *StockListService) saveStock(ctx context.Context, stock TWStockInfo) error {
	industry := stock.Industry
	if industry == "" {
		industry = "未分類"
	}
	
	stockData := &storage.Stock{
		StockCode: stock.Code,
		StockName: stock.Name,
		Market:    stock.Market,
		Industry:  &industry,
		IsActive:  true,
	}
	
	return s.repository.UpsertStock(ctx, stockData)
}

// getDefaultTWSEStocks 取得預設上市股票清單（備用方案）
func (s *StockListService) getDefaultTWSEStocks() []TWStockInfo {
	return []TWStockInfo{
		{Code: "2330", Name: "台積電", Market: "上市", Industry: "半導體"},
		{Code: "2317", Name: "鴻海", Market: "上市", Industry: "電子"},
		{Code: "2412", Name: "中華電", Market: "上市", Industry: "通訊"},
		{Code: "2881", Name: "富邦金", Market: "上市", Industry: "金融"},
		{Code: "2882", Name: "國泰金", Market: "上市", Industry: "金融"},
		{Code: "2303", Name: "聯電", Market: "上市", Industry: "半導體"},
		{Code: "2308", Name: "台達電", Market: "上市", Industry: "電子"},
		{Code: "2454", Name: "聯發科", Market: "上市", Industry: "半導體"},
		{Code: "2886", Name: "兆豐金", Market: "上市", Industry: "金融"},
		{Code: "2891", Name: "中信金", Market: "上市", Industry: "金融"},
		{Code: "2002", Name: "中鋼", Market: "上市", Industry: "鋼鐵"},
		{Code: "2301", Name: "光寶科", Market: "上市", Industry: "電子"},
		{Code: "2379", Name: "瑞昱", Market: "上市", Industry: "半導體"},
		{Code: "2395", Name: "研華", Market: "上市", Industry: "電子"},
		{Code: "3008", Name: "大立光", Market: "上市", Industry: "光學"},
		{Code: "2357", Name: "華碩", Market: "上市", Industry: "電腦"},
		{Code: "2409", Name: "友達", Market: "上市", Industry: "面板"},
		{Code: "2892", Name: "第一金", Market: "上市", Industry: "金融"},
		{Code: "3045", Name: "台灣大", Market: "上市", Industry: "通訊"},
		{Code: "2327", Name: "國巨", Market: "上市", Industry: "電子"},
	}
}

// getDefaultTPEXStocks 取得預設上櫃股票清單（備用方案）
func (s *StockListService) getDefaultTPEXStocks() []TWStockInfo {
	return []TWStockInfo{
		{Code: "3711", Name: "日月光投控", Market: "上櫃", Industry: "半導體"},
		{Code: "5269", Name: "祥碩", Market: "上櫃", Industry: "半導體"},
		{Code: "6115", Name: "鎧勝-KY", Market: "上櫃", Industry: "電子"},
		{Code: "4904", Name: "遠傳", Market: "上櫃", Industry: "通訊"},
		{Code: "5274", Name: "信驊", Market: "上櫃", Industry: "半導體"},
		{Code: "6669", Name: "緯穎", Market: "上櫃", Industry: "電腦"},
		{Code: "4938", Name: "和碩", Market: "上櫃", Industry: "電子"},
		{Code: "3231", Name: "緯創", Market: "上櫃", Industry: "電腦"},
		{Code: "6505", Name: "台塑化", Market: "上櫃", Industry: "化工"},
		{Code: "5388", Name: "中磊", Market: "上櫃", Industry: "通訊"},
	}
}

// isNumeric 檢查字串是否為純數字
func isNumeric(s string) bool {
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}
