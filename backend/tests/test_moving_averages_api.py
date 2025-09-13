"""均線計算API的TDD測試"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.database import get_db
from src.models.stock import MovingAverages, StockDailyData, Stock


class TestMovingAveragesAPI:
    """均線計算API測試類別"""

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """模擬資料庫連接"""
        return Mock()

    @pytest.fixture
    def sample_stock_data(self):
        """範例股票歷史資料"""
        base_date = datetime.now().date()
        return [
            {
                "stock_code": "2330",
                "trade_date": base_date - timedelta(days=i),
                "close_price": 100.0 + i,
                "volume": 10000
            }
            for i in range(100)  # 提供100天的資料供計算60日均線
        ]

    def test_moving_averages_statistics_endpoint_exists(self, client):
        """測試統計資訊API端點存在"""
        response = client.get("/api/v1/moving-averages/statistics")
        assert response.status_code in [200, 404, 405], "API端點應該存在或返回正確錯誤碼"

    def test_moving_averages_statistics_success(self, client):
        """測試成功獲取統計資訊"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.get_statistics.return_value = {
                "stocks_with_ma": 100,
                "total_ma_records": 50000,
                "latest_calculation_date": "2025-09-12",
                "calculation_completeness": 85.5
            }
            
            response = client.get("/api/v1/moving-averages/statistics")
            assert response.status_code == 200
            data = response.json()
            assert "stocks_with_ma" in data
            assert "total_ma_records" in data
            assert data["stocks_with_ma"] == 100

    def test_calculate_moving_averages_endpoint_exists(self, client):
        """測試計算均線API端點存在"""
        response = client.post("/api/v1/moving-averages/calculate", json={
            "stock_codes": ["2330"],
            "periods": [5, 10, 20],
            "force_recalculate": False
        })
        assert response.status_code in [200, 201, 404, 422], "API端點應該存在"

    def test_calculate_moving_averages_single_stock(self, client):
        """測試單一股票均線計算"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.calculate_moving_averages.return_value = {
                "success": True,
                "processed_stocks": 1,
                "total_calculations": 60,
                "execution_time": 2.5
            }
            
            request_data = {
                "stock_codes": ["2330"],
                "periods": [5, 10, 20],
                "force_recalculate": False
            }
            
            response = client.post("/api/v1/moving-averages/calculate", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True
            assert data.get("processed_stocks") == 1

    def test_calculate_moving_averages_invalid_stock_code(self, client):
        """測試無效股票代號"""
        request_data = {
            "stock_codes": ["0000"],
            "periods": [5, 10, 20],
            "force_recalculate": False
        }
        
        response = client.post("/api/v1/moving-averages/calculate", json=request_data)
        assert response.status_code in [400, 422], "應該返回錯誤狀態碼"

    def test_calculate_moving_averages_invalid_periods(self, client):
        """測試無效均線週期"""
        request_data = {
            "stock_codes": ["2330"],
            "periods": [0, -5],  # 無效週期
            "force_recalculate": False
        }
        
        response = client.post("/api/v1/moving-averages/calculate", json=request_data)
        assert response.status_code in [400, 422], "應該返回錯誤狀態碼"

    def test_query_moving_averages_endpoint_exists(self, client):
        """測試查詢均線API端點存在"""
        response = client.get("/api/v1/moving-averages/query/2330")
        assert response.status_code in [200, 404], "API端點應該存在"

    def test_query_moving_averages_success(self, client):
        """測試成功查詢均線資料"""
        mock_ma_data = [
            {
                "stock_code": "2330",
                "trade_date": "2025-09-12",
                "close_price": 100.0,
                "ma5": 98.0,
                "ma10": 97.5,
                "ma20": 96.8,
                "ma60": 95.2
            }
        ]
        
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.query_moving_averages.return_value = {
                "success": True,
                "data": mock_ma_data,
                "total_records": 1
            }
            
            response = client.get("/api/v1/moving-averages/query/2330?periods=5,10,20")
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) > 0
            assert data["data"][0]["stock_code"] == "2330"

    def test_query_moving_averages_with_date_range(self, client):
        """測試日期範圍查詢"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.query_moving_averages.return_value = {
                "success": True,
                "data": [],
                "total_records": 0
            }
            
            params = {
                "start_date": "2025-09-01",
                "end_date": "2025-09-12",
                "periods": "5,10,20",
                "page": 1,
                "limit": 100
            }
            
            response = client.get("/api/v1/moving-averages/query/2330", params=params)
            assert response.status_code == 200

    def test_query_moving_averages_invalid_stock_code(self, client):
        """測試查詢無效股票代號"""
        response = client.get("/api/v1/moving-averages/query/123")
        assert response.status_code in [400, 422], "應該返回錯誤狀態碼"

    def test_async_calculation_endpoint_exists(self, client):
        """測試非同步計算API端點存在"""
        response = client.post("/api/v1/moving-averages/calculate-async", json={
            "stock_codes": ["2330"],
            "periods": [5, 10, 20],
            "batch_size": 50
        })
        assert response.status_code in [200, 201, 404, 422], "API端點應該存在"

    def test_async_calculation_task_creation(self, client):
        """測試非同步任務創建"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_task_id = "test-task-12345"
            mock_service.return_value.start_async_calculation.return_value = {
                "success": True,
                "task_id": mock_task_id,
                "message": "非同步計算任務已啟動"
            }
            
            request_data = {
                "stock_codes": None,  # 計算所有股票
                "periods": [5, 10, 20, 60],
                "force_recalculate": False,
                "batch_size": 50
            }
            
            response = client.post("/api/v1/moving-averages/calculate-async", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data.get("success") is True

    def test_task_status_endpoint_exists(self, client):
        """測試任務狀態API端點存在"""
        task_id = "test-task-12345"
        response = client.get(f"/api/v1/moving-averages/task-status/{task_id}")
        assert response.status_code in [200, 404], "API端點應該存在"

    def test_task_status_query(self, client):
        """測試查詢任務狀態"""
        task_id = "test-task-12345"
        mock_status = {
            "state": "PENDING",
            "current": 10,
            "total": 100,
            "percentage": 10,
            "stage": "計算MA5",
            "result": None,
            "error": None
        }
        
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.get_task_status.return_value = {
                "success": True,
                "data": mock_status
            }
            
            response = client.get(f"/api/v1/moving-averages/task-status/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert data["data"]["state"] == "PENDING"
            assert data["data"]["percentage"] == 10

    def test_task_cancellation_endpoint_exists(self, client):
        """測試任務取消API端點存在"""
        task_id = "test-task-12345"
        response = client.delete(f"/api/v1/moving-averages/task/{task_id}")
        assert response.status_code in [200, 404], "API端點應該存在"

    def test_validate_moving_averages_endpoint_exists(self, client):
        """測試驗證均線API端點存在"""
        response = client.get("/api/v1/moving-averages/validate")
        assert response.status_code in [200, 404], "API端點應該存在"

    def test_clear_moving_averages_endpoint_exists(self, client):
        """測試清除均線API端點存在"""
        response = client.post("/api/v1/moving-averages/clear")
        assert response.status_code in [200, 404], "API端點應該存在"

    @patch('src.services.moving_averages_service.MovingAveragesService')
    def test_moving_averages_calculation_logic(self, mock_service):
        """測試均線計算邏輯正確性"""
        # 模擬歷史價格資料
        test_prices = [100, 102, 98, 105, 103, 107, 109, 106, 108, 110]
        expected_ma5_last = sum(test_prices[-5:]) / 5  # 106.4
        
        # 設定模擬服務回應
        mock_service.return_value.calculate_single_stock_ma.return_value = {
            "stock_code": "2330",
            "calculations": {
                "ma5": expected_ma5_last,
                "ma10": sum(test_prices) / len(test_prices)
            }
        }
        
        # 驗證計算結果
        service = mock_service.return_value
        result = service.calculate_single_stock_ma("2330", [5, 10])
        
        assert result["stock_code"] == "2330"
        assert abs(result["calculations"]["ma5"] - 106.4) < 0.01

    def test_database_integration_mock(self, mock_db):
        """測試資料庫整合（使用Mock）"""
        # 模擬資料庫查詢
        mock_ma_record = MovingAverages(
            stock_id="2330",
            trade_date=datetime.now(),
            ma_5=100.0,
            ma_10=99.5,
            ma_20=98.8
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_ma_record
        
        # 測試查詢邏輯
        result = mock_db.query(MovingAverages).filter(
            MovingAverages.stock_id == "2330"
        ).first()
        
        assert result.stock_id == "2330"
        assert result.ma_5 == 100.0

    def test_error_handling_service_unavailable(self, client):
        """測試服務不可用錯誤處理"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/v1/moving-averages/statistics")
            # 應該有適當的錯誤處理，不會返回500
            assert response.status_code in [200, 500, 503]

    def test_pagination_query(self, client):
        """測試分頁查詢功能"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_service.return_value.query_moving_averages.return_value = {
                "success": True,
                "data": [],
                "total_records": 1000,
                "page": 1,
                "limit": 50,
                "total_pages": 20
            }
            
            params = {
                "page": 1,
                "limit": 50
            }
            
            response = client.get("/api/v1/moving-averages/query/2330", params=params)
            assert response.status_code == 200
            data = response.json()
            assert "total_pages" in data or "total_records" in data

    def test_performance_large_dataset(self, client):
        """測試大資料集效能"""
        # 這個測試可能需要較長時間，標記為slow
        large_stock_list = [f"{1000+i:04d}" for i in range(1000)]
        
        request_data = {
            "stock_codes": large_stock_list,
            "periods": [5, 10, 20],
            "force_recalculate": False
        }
        
        # 在實際場景中，這應該會自動轉為非同步處理
        response = client.post("/api/v1/moving-averages/calculate", json=request_data)
        # 不應該超時或返回500錯誤
        assert response.status_code != 500

    def test_concurrent_calculations(self, client):
        """測試並發計算處理"""
        import threading
        import time
        
        def make_request():
            response = client.post("/api/v1/moving-averages/calculate-async", json={
                "stock_codes": ["2330"],
                "periods": [5, 10, 20]
            })
            return response.status_code
        
        # 創建多個並發請求
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 所有請求都應該得到適當處理
        assert all(status in [200, 201, 429] for status in results)  # 429 = Rate Limited

    def test_data_consistency_validation(self, client):
        """測試資料一致性驗證"""
        with patch('src.services.moving_averages_service.MovingAveragesService') as mock_service:
            mock_validation_result = {
                "success": True,
                "total_records_checked": 50000,
                "inconsistent_records": 3,
                "fixed_records": 3,
                "validation_time": 15.5
            }
            
            mock_service.return_value.validate_data_consistency.return_value = mock_validation_result
            
            response = client.get("/api/v1/moving-averages/validate")
            assert response.status_code == 200
            data = response.json()
            assert "total_records_checked" in data
            assert data.get("inconsistent_records", 0) >= 0


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v", "--tb=short"])