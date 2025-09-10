"""股票歷史資料查詢API的TDD測試

本測試檔案涵蓋股票歷史資料查詢API的各種情境：
- 查詢特定股票的歷史資料
- 日期範圍篩選
- 分頁功能
- 排序功能
- 錯誤處理
- 效能測試

執行測試：pytest tests/test_stock_history_api.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.stock import StockDailyData, Stock
from src.core.database import get_db


class TestStockHistoryAPI:
    """股票歷史資料查詢API測試類別"""
    
    @pytest.fixture
    def client(self):
        """建立測試用的FastAPI客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """建立模擬資料庫會話"""
        return Mock()
    
    @pytest.fixture
    def sample_stock_data(self):
        """建立測試用的股票歷史資料"""
        base_date = datetime(2024, 1, 1)
        return [
            {
                "stock_id": "2330",
                "trade_date": base_date + timedelta(days=i),
                "open_price": 580.0 + i,
                "high_price": 590.0 + i,
                "low_price": 570.0 + i,
                "close_price": 585.0 + i,
                "volume": 10000000 + i * 100000,
                "adjusted_close": 585.0 + i
            }
            for i in range(30)  # 30天的測試資料
        ]
    
    def test_get_stock_history_api_endpoint_exists(self, client):
        """測試：股票歷史資料查詢API端點存在"""
        # 測試GET /api/v1/data/history/{symbol}端點是否存在
        response = client.get("/api/v1/data/history/2330")
        # 應該回傳200或者有意義的錯誤碼，而不是404
        assert response.status_code != 404, "API端點不存在"
    
    def test_get_stock_history_valid_symbol(self, client):
        """測試：使用有效股票代號查詢歷史資料"""
        # 查詢台積電(2330)的歷史資料
        response = client.get("/api/v1/data/history/2330")
        
        # 應該回傳成功狀態
        assert response.status_code == 200
        
        data = response.json()
        # 檢查回傳資料結構
        assert "status" in data
        assert "stock_symbol" in data
        assert "data" in data
        assert "total_records" in data
        
        # 檢查股票代號正確
        assert data["stock_symbol"] == "2330"
        
        # 檢查資料陣列結構
        if data["total_records"] > 0:
            first_record = data["data"][0]
            required_fields = ["trade_date", "open_price", "high_price", 
                             "low_price", "close_price", "volume", "adjusted_close"]
            for field in required_fields:
                assert field in first_record, f"缺少必要欄位：{field}"
    
    def test_get_stock_history_invalid_symbol_format(self, client):
        """測試：使用無效的股票代號格式"""
        invalid_symbols = ["123", "12345", "0123", "abc1", ""]
        
        for symbol in invalid_symbols:
            response = client.get(f"/api/v1/data/history/{symbol}")
            assert response.status_code == 400, f"股票代號 {symbol} 應該回傳400錯誤"
            
            data = response.json()
            assert "detail" in data
            assert "Invalid stock symbol" in data["detail"]
    
    def test_get_stock_history_with_date_range(self, client):
        """測試：使用日期範圍篩選查詢歷史資料"""
        # 查詢特定日期範圍的資料
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        response = client.get(
            f"/api/v1/data/history/2330",
            params={"start_date": start_date, "end_date": end_date}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        # 檢查篩選條件有被正確處理
        assert "start_date" in data.get("query_params", {})
        assert "end_date" in data.get("query_params", {})
    
    def test_get_stock_history_with_pagination(self, client):
        """測試：分頁功能"""
        # 測試第一頁
        response = client.get(
            "/api/v1/data/history/2330",
            params={"page": 1, "limit": 10}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        # 檢查分頁資訊
        assert "pagination" in data
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination
        
        # 資料數量不應超過limit
        if data["total_records"] > 0:
            assert len(data["data"]) <= 10
    
    def test_get_stock_history_sorting(self, client):
        """測試：資料排序功能"""
        # 測試按日期降序排列（最新的在前面）
        response = client.get(
            "/api/v1/data/history/2330",
            params={"sort_by": "trade_date", "sort_order": "desc"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        if data["total_records"] >= 2:
            # 檢查是否按日期降序排列
            dates = [record["trade_date"] for record in data["data"]]
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i + 1], "資料未按日期降序排列"
    
    def test_get_stock_history_nonexistent_stock(self, client):
        """測試：查詢不存在的股票"""
        # 使用格式正確但不存在的股票代號
        response = client.get("/api/v1/data/history/9999")
        
        assert response.status_code == 200  # 應該成功但回傳空資料
        
        data = response.json()
        assert data["status"] == "success"
        assert data["total_records"] == 0
        assert len(data["data"]) == 0
    
    def test_get_stock_history_date_validation(self, client):
        """測試：日期格式驗證"""
        # 測試無效的日期格式
        invalid_dates = ["2024-13-01", "2024/01/01", "invalid-date", ""]
        
        for invalid_date in invalid_dates:
            response = client.get(
                "/api/v1/data/history/2330",
                params={"start_date": invalid_date}
            )
            assert response.status_code == 400, f"無效日期 {invalid_date} 應該回傳400錯誤"
    
    def test_get_stock_history_pagination_bounds(self, client):
        """測試：分頁參數邊界值"""
        # 測試無效的分頁參數
        invalid_params = [
            {"page": 0},  # 頁數不能為0
            {"page": -1}, # 頁數不能為負數
            {"limit": 0}, # 每頁數量不能為0
            {"limit": -1}, # 每頁數量不能為負數
            {"limit": 1001} # 每頁數量不能超過上限
        ]
        
        for params in invalid_params:
            response = client.get("/api/v1/data/history/2330", params=params)
            assert response.status_code == 400, f"無效參數 {params} 應該回傳400錯誤"
    
    @patch('src.services.stock_history_service.StockHistoryService')
    def test_get_stock_history_service_integration(self, mock_service, client, sample_stock_data):
        """測試：與股票歷史資料服務的整合"""
        # 設定模擬服務回傳資料
        mock_service_instance = mock_service.return_value
        mock_service_instance.get_stock_history.return_value = {
            "data": sample_stock_data[:10],
            "total_records": len(sample_stock_data),
            "pagination": {
                "page": 1,
                "limit": 10,
                "total_pages": 3,
                "has_next": True,
                "has_previous": False
            }
        }
        
        # 使用dependency injection覆蓋服務
        with patch('src.api.endpoints.history.get_stock_history_service',
                  return_value=mock_service_instance):
            response = client.get("/api/v1/data/history/2330")
        
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data"]) == 10
        assert data["total_records"] == 30
        
        # 驗證服務方法被正確呼叫
        mock_service_instance.get_stock_history.assert_called_once()
    
    def test_get_stock_history_performance(self, client):
        """測試：API回應效能"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/data/history/2330", params={"limit": 100})
        end_time = time.time()
        
        # API回應時間應該在合理範圍內（假設3秒以內）
        response_time = end_time - start_time
        assert response_time < 3.0, f"API回應時間過長：{response_time:.2f}秒"
        
        assert response.status_code == 200
    
    def test_get_stock_history_data_types(self, client):
        """測試：回傳資料的類型正確性"""
        response = client.get("/api/v1/data/history/2330", params={"limit": 1})
        
        if response.status_code == 200:
            data = response.json()
            if data["total_records"] > 0:
                record = data["data"][0]
                
                # 檢查價格欄位是數值型態
                assert isinstance(record["open_price"], (int, float))
                assert isinstance(record["high_price"], (int, float))
                assert isinstance(record["low_price"], (int, float))
                assert isinstance(record["close_price"], (int, float))
                assert isinstance(record["adjusted_close"], (int, float))
                
                # 檢查成交量是整數
                assert isinstance(record["volume"], int)
                
                # 檢查日期是字串格式
                assert isinstance(record["trade_date"], str)
                
                # 檢查價格關係正確性
                assert record["high_price"] >= record["low_price"]
                assert record["low_price"] <= record["open_price"] <= record["high_price"]
                assert record["low_price"] <= record["close_price"] <= record["high_price"]


class TestStockHistoryAPIErrorHandling:
    """股票歷史資料查詢API錯誤處理測試"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_database_connection_error(self, client):
        """測試：資料庫連線錯誤處理"""
        with patch('src.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("資料庫連線失敗")
            
            response = client.get("/api/v1/data/history/2330")
            assert response.status_code == 500
            
            data = response.json()
            assert "detail" in data
    
    def test_service_timeout_handling(self, client):
        """測試：服務超時處理"""
        with patch('src.services.stock_history_service.StockHistoryService') as mock_service:
            mock_service.return_value.get_stock_history.side_effect = TimeoutError("查詢超時")
            
            response = client.get("/api/v1/data/history/2330")
            assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])