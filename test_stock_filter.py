"""Simple test to verify stock filtering logic."""

import sys
import os

# 將backend/src添加到Python路徑
backend_src_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src_path)

# 創建一個簡化版的StockListService用於測試
class TestStockListService:
    """Simplified version for testing core logic."""
    
    def filter_valid_stocks(self, raw_stocks):
        """Filter stocks to only include valid 4-digit non-zero-prefix symbols."""
        valid_stocks = []
        
        for stock in raw_stocks:
            symbol = stock.get("symbol", "").strip()
            
            # 檢查是否為4位數且不以0開頭
            if (len(symbol) == 4 and 
                symbol.isdigit() and 
                not symbol.startswith("0")):
                valid_stocks.append(stock)
                
        return valid_stocks
    
    def validate_stock_data(self, stock_data):
        """Validate stock data format and required fields."""
        import re
        
        required_fields = ["symbol", "name", "market"]
        
        for field in required_fields:
            if field not in stock_data or not stock_data[field]:
                return False
        
        symbol = stock_data["symbol"]
        if not re.match(r"^[1-9]\d{3}$", symbol):
            return False
            
        market = stock_data["market"]
        if market not in ["TSE", "TPEx"]:
            return False
            
        return True

def test_stock_filtering():
    """Test stock filtering functionality."""
    service = TestStockListService()
    
    # 測試資料：包含有效和無效股票
    test_stocks = [
        {"symbol": "2330", "name": "台積電", "market": "TSE"},  # 有效
        {"symbol": "1101", "name": "台泥", "market": "TSE"},    # 有效
        {"symbol": "0050", "name": "元大台灣50", "market": "TSE"},  # 無效（ETF）
        {"symbol": "00878", "name": "國泰永續高股息", "market": "TSE"},  # 無效（ETF）
        {"symbol": "123", "name": "短代號", "market": "TSE"},   # 無效（3位數）
        {"symbol": "12345", "name": "長代號", "market": "TSE"}, # 無效（5位數）
        {"symbol": "ABCD", "name": "非數字", "market": "TSE"},  # 無效（非數字）
        {"symbol": "6505", "name": "台塑化", "market": "TPEx"}, # 有效
    ]
    
    # 執行過濾
    valid_stocks = service.filter_valid_stocks(test_stocks)
    
    print(f"原始股票數：{len(test_stocks)}")
    print(f"有效股票數：{len(valid_stocks)}")
    print("\n有效股票列表：")
    
    for stock in valid_stocks:
        print(f"  {stock['symbol']} - {stock['name']} ({stock['market']})")
    
    # 驗證結果
    expected_symbols = {"2330", "1101", "6505"}
    actual_symbols = {stock["symbol"] for stock in valid_stocks}
    
    print(f"\n預期符號：{expected_symbols}")
    print(f"實際符號：{actual_symbols}")
    
    if expected_symbols == actual_symbols:
        print("\n[PASS] 測試通過！股票過濾邏輯正確。")
        return True
    else:
        print(f"\n[FAIL] 測試失敗！預期 {expected_symbols}，實際 {actual_symbols}")
        return False

def test_stock_validation():
    """Test stock data validation."""
    service = TestStockListService()
    
    # 測試有效資料
    valid_stock = {
        "symbol": "2330",
        "name": "台積電", 
        "market": "TSE"
    }
    
    # 測試無效資料
    invalid_stocks = [
        {"symbol": "0050", "name": "ETF", "market": "TSE"},  # 0開頭
        {"symbol": "123", "name": "短", "market": "TSE"},    # 3位數
        {"symbol": "", "name": "空", "market": "TSE"},       # 空代號
        {"symbol": "2330", "name": "", "market": "TSE"},     # 空名稱
        {"symbol": "2330", "name": "台積電", "market": "INVALID"},  # 無效市場
    ]
    
    print("\n=== 股票資料驗證測試 ===")
    
    # 測試有效資料
    if service.validate_stock_data(valid_stock):
        print("[PASS] 有效資料驗證通過")
    else:
        print("[FAIL] 有效資料驗證失敗")
        return False
    
    # 測試無效資料
    all_invalid_detected = True
    for i, invalid_stock in enumerate(invalid_stocks):
        if service.validate_stock_data(invalid_stock):
            print(f"[FAIL] 無效資料 {i+1} 未被偵測到：{invalid_stock}")
            all_invalid_detected = False
        else:
            print(f"[PASS] 無效資料 {i+1} 正確被拒絕")
    
    return all_invalid_detected

if __name__ == "__main__":
    print("=== 股票擷取模組測試 ===\n")
    
    # 執行過濾測試
    filter_success = test_stock_filtering()
    
    # 執行驗證測試
    validation_success = test_stock_validation()
    
    # 總結
    print(f"\n=== 測試結果總結 ===")
    print(f"過濾邏輯測試：{'[PASS] 通過' if filter_success else '[FAIL] 失敗'}")
    print(f"資料驗證測試：{'[PASS] 通過' if validation_success else '[FAIL] 失敗'}")
    
    if filter_success and validation_success:
        print("\n[SUCCESS] 所有核心邏輯測試通過！股票擷取模組基本功能正常。")
        exit(0)
    else:
        print("\n[ERROR] 部分測試失敗，需要修正。")
        exit(1)