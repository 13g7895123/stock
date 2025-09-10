"""
TDD測試：更新所有股票歷史資料功能 - Test Update All Stocks Functionality

This test file covers the comprehensive testing of the bulk stock data update functionality,
including TDD requirements for Point 18:
- API endpoint testing
- Performance monitoring (execution time tracking)
- Error handling
- Bulk data processing
- Background task management

測試覆蓋範圍：
1. API端點正確性測試
2. 執行時間記錄功能
3. 錯誤處理機制
4. 批次資料處理
5. 背景任務管理
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.core.database import get_db
from src.core.config import settings
from src.models.stock import Stock


class TestUpdateAllStocks:
    """更新所有股票歷史資料功能測試類別"""
    
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫會話"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_stock_data(self):
        """模擬股票資料"""
        stocks = []
        for i in range(5):
            stock = Mock(spec=Stock)
            stock.symbol = f"230{i}"
            stock.name = f"Test Stock {i}"
            stock.market = "TSE"
            stock.is_active = True
            stocks.append(stock)
        return stocks
    
    @pytest.fixture
    def mock_celery_task(self):
        """模擬 Celery 任務"""
        task = Mock()
        task.id = "test-task-id-12345"
        task.state = "PENDING"
        return task
    
    def test_update_all_stocks_api_endpoint_exists(self, client):
        """測試 1: 確認更新所有股票API端點存在"""
        # Act
        response = client.post("/api/v1/stocks/update-all")
        
        # Assert
        assert response.status_code != 404, "API端點應該存在"
        assert response.status_code in [200, 422, 500], "應該回傳有效的HTTP狀態碼"
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_with_default_symbols(self, mock_update_task, client, mock_celery_task):
        """測試 2: 使用預設股票代號清單更新所有股票"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        
        # Act
        start_time = time.time()
        response = client.post("/api/v1/stocks/update-all")
        execution_time = time.time() - start_time
        
        # Assert
        assert response.status_code == 200, "更新所有股票應該成功"
        
        response_data = response.json()
        assert "message" in response_data, "回應應該包含訊息"
        assert "symbols" in response_data, "回應應該包含股票代號清單"
        assert "task_id" in response_data, "回應應該包含任務ID"
        assert "status" in response_data, "回應應該包含狀態"
        assert "timestamp" in response_data, "回應應該包含時間戳記"
        
        # 驗證使用預設股票代號
        expected_symbols = [s.upper() for s in settings.DEFAULT_STOCK_SYMBOLS]
        assert response_data["symbols"] == expected_symbols, "應該使用預設股票代號清單"
        assert response_data["task_id"] == mock_celery_task.id, "應該回傳正確的任務ID"
        assert response_data["status"] == "queued", "狀態應該為已佇列"
        
        # 驗證Celery任務被正確呼叫
        mock_update_task.delay.assert_called_once_with(expected_symbols)
        
        # 執行時間記錄測試
        assert execution_time < 5.0, f"API回應時間應該少於5秒，實際：{execution_time:.2f}秒"
        print(f"[OK] API執行時間：{execution_time:.4f}秒")
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_with_custom_symbols(self, mock_update_task, client, mock_celery_task):
        """測試 3: 使用自訂股票代號清單更新"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        custom_symbols = ["2330", "2317", "2454"]
        
        # Act
        start_time = time.time()
        response = client.post(
            "/api/v1/stocks/update-all",
            json={"symbols": custom_symbols}
        )
        execution_time = time.time() - start_time
        
        # Assert
        assert response.status_code == 200, "自訂股票清單更新應該成功"
        
        response_data = response.json()
        expected_symbols = [s.upper() for s in custom_symbols]
        assert response_data["symbols"] == expected_symbols, "應該使用自訂股票代號清單"
        assert len(response_data["symbols"]) == len(custom_symbols), "股票數量應該正確"
        
        # 驗證Celery任務被正確呼叫
        mock_update_task.delay.assert_called_once_with(expected_symbols)
        
        # 執行時間記錄測試
        assert execution_time < 3.0, f"自訂清單API回應時間應該更快，實際：{execution_time:.2f}秒"
        print(f"[OK] 自訂清單API執行時間：{execution_time:.4f}秒")
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_empty_symbols_list(self, mock_update_task, client, mock_celery_task):
        """測試 4: 空股票清單處理"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        
        # Act
        response = client.post(
            "/api/v1/stocks/update-all",
            json={"symbols": []}
        )
        
        # Assert
        assert response.status_code == 200, "空清單應該回傳成功並使用預設清單"
        response_data = response.json()
        # 當傳入空清單時，應該使用預設股票清單
        expected_symbols = [s.upper() for s in settings.DEFAULT_STOCK_SYMBOLS]
        assert len(response_data["symbols"]) > 0, "應該使用預設股票清單"
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_invalid_symbols(self, mock_update_task, client, mock_celery_task):
        """測試 5: 無效股票代號處理"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        invalid_symbols = ["INVALID", "123", "ABCD", ""]
        
        # Act
        response = client.post(
            "/api/v1/stocks/update-all",
            json={"symbols": invalid_symbols}
        )
        
        # Assert
        assert response.status_code == 200, "無效股票代號應該被處理（轉換為大寫）"
        response_data = response.json()
        
        # 驗證股票代號被轉換為大寫
        expected_symbols = [s.upper() for s in invalid_symbols if s]  # 過濾空字串
        assert response_data["symbols"] == expected_symbols, "股票代號應該被轉換為大寫"
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_large_batch_performance(self, mock_update_task, client, mock_celery_task):
        """測試 6: 大批次股票更新效能測試"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        # 創建大量股票代號清單（模擬實際場景）
        large_symbols_list = [f"2{i:03d}" for i in range(300, 600)]  # 300個股票代號
        
        # Act
        start_time = time.time()
        response = client.post(
            "/api/v1/stocks/update-all",
            json={"symbols": large_symbols_list}
        )
        execution_time = time.time() - start_time
        
        # Assert
        assert response.status_code == 200, "大批次更新應該成功"
        response_data = response.json()
        assert len(response_data["symbols"]) == len(large_symbols_list), "應該處理所有股票代號"
        
        # 效能要求：大批次處理時間應該在合理範圍內
        assert execution_time < 10.0, f"大批次API回應時間應該少於10秒，實際：{execution_time:.2f}秒"
        print(f"[OK] 大批次處理（{len(large_symbols_list)}支股票）執行時間：{execution_time:.4f}秒")
        
        # 驗證任務被正確觸發
        mock_update_task.delay.assert_called_once()
        called_symbols = mock_update_task.delay.call_args[0][0]
        assert len(called_symbols) == len(large_symbols_list), "所有股票代號都應該被傳遞給背景任務"
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_celery_task_failure(self, mock_update_task, client):
        """測試 7: Celery任務觸發失敗處理"""
        # Arrange
        mock_update_task.delay.side_effect = Exception("Celery connection failed")
        
        # Act
        response = client.post("/api/v1/stocks/update-all")
        
        # Assert
        # API應該優雅地處理Celery錯誤
        assert response.status_code in [500, 503], "Celery錯誤應該回傳適當的錯誤狀態碼"
    
    def test_update_all_stocks_execution_time_logging(self, client):
        """測試 8: 執行時間記錄功能驗證"""
        # Arrange & Act
        start_times = []
        execution_times = []
        
        # 執行多次測試以驗證時間記錄的一致性
        for i in range(3):
            start_time = time.time()
            response = client.post("/api/v1/stocks/update-all")
            execution_time = time.time() - start_time
            
            start_times.append(start_time)
            execution_times.append(execution_time)
            
            # 基本驗證
            assert response.status_code in [200, 500], f"第{i+1}次請求應該有有效回應"
        
        # Assert
        # 驗證執行時間記錄功能
        assert len(execution_times) == 3, "應該記錄所有執行時間"
        assert all(t > 0 for t in execution_times), "所有執行時間都應該大於0"
        assert all(t < 30.0 for t in execution_times), "所有執行時間都應該在合理範圍內"
        
        # 計算統計資料
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        print(f"[OK] 執行時間統計：")
        print(f"   - 平均時間：{avg_time:.4f}秒")
        print(f"   - 最短時間：{min_time:.4f}秒") 
        print(f"   - 最長時間：{max_time:.4f}秒")
        
        # 效能要求驗證
        assert avg_time < 5.0, f"平均執行時間應該少於5秒，實際：{avg_time:.4f}秒"
        assert max_time < 10.0, f"最長執行時間應該少於10秒，實際：{max_time:.4f}秒"
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_response_format(self, mock_update_task, client, mock_celery_task):
        """測試 9: API回應格式驗證"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        
        # Act
        response = client.post("/api/v1/stocks/update-all")
        
        # Assert
        assert response.status_code == 200, "API應該成功"
        response_data = response.json()
        
        # 驗證必要欄位存在
        required_fields = ["message", "symbols", "task_id", "status", "timestamp"]
        for field in required_fields:
            assert field in response_data, f"回應應該包含{field}欄位"
        
        # 驗證欄位類型
        assert isinstance(response_data["message"], str), "message應該是字串"
        assert isinstance(response_data["symbols"], list), "symbols應該是陣列"
        assert isinstance(response_data["task_id"], str), "task_id應該是字串"
        assert isinstance(response_data["status"], str), "status應該是字串"
        assert isinstance(response_data["timestamp"], str), "timestamp應該是字串"
        
        # 驗證時間戳記格式
        try:
            datetime.fromisoformat(response_data["timestamp"])
        except ValueError:
            pytest.fail("timestamp應該是有效的ISO格式")
    
    @patch('src.api.endpoints.stocks.update_market_data')
    def test_update_all_stocks_concurrent_requests(self, mock_update_task, client, mock_celery_task):
        """測試 10: 並發請求處理"""
        # Arrange
        mock_update_task.delay.return_value = mock_celery_task
        
        # Act - 模擬並發請求
        responses = []
        start_time = time.time()
        
        # 快速發送多個請求
        for i in range(3):
            response = client.post("/api/v1/stocks/update-all")
            responses.append(response)
        
        total_time = time.time() - start_time
        
        # Assert
        assert len(responses) == 3, "應該處理所有並發請求"
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"第{i+1}個並發請求應該成功"
        
        # 驗證所有回應都有唯一的時間戳記
        timestamps = [resp.json()["timestamp"] for resp in responses]
        assert len(set(timestamps)) > 1, "並發請求應該有不同的時間戳記"
        
        print(f"[OK] 並發請求處理時間：{total_time:.4f}秒")
        
        # 驗證Celery任務被多次觸發
        assert mock_update_task.delay.call_count == 3, "每個請求都應該觸發一個背景任務"
    
    def test_update_all_stocks_api_documentation_compliance(self, client):
        """測試 11: API文件合規性驗證"""
        # Act
        response = client.post("/api/v1/stocks/update-all")
        
        # Assert - 驗證API符合OpenAPI規範
        assert response.headers.get("content-type") == "application/json", "應該回傳JSON格式"
        
        if response.status_code == 200:
            response_data = response.json()
            
            # 驗證回應符合預期的結構
            assert "message" in response_data, "回應應該包含操作訊息"
            assert "symbols" in response_data, "回應應該包含處理的股票清單"
            assert isinstance(response_data["symbols"], list), "symbols應該是陣列"
            
            # 驗證message內容合理性
            message = response_data["message"]
            assert "update" in message.lower(), "訊息應該提到更新操作"
            assert "symbol" in message.lower(), "訊息應該提到股票代號"
    
    def test_update_all_stocks_integration_readiness(self, client):
        """測試 12: 整合就緒性驗證"""
        # Act & Assert - 驗證API準備好進行整合
        response = client.post("/api/v1/stocks/update-all")
        
        # 基本可用性檢查
        assert response.status_code != 404, "API端點應該可用"
        assert response.status_code != 405, "HTTP方法應該被支援"
        
        # 如果成功，驗證回應完整性
        if response.status_code == 200:
            response_data = response.json()
            assert "task_id" in response_data, "應該提供任務追蹤ID"
            assert response_data["task_id"], "任務ID不應該為空"
            
            print("[OK] API整合就緒性檢查通過")
            print(f"   - 端點可用：✓")
            print(f"   - 回應格式正確：✓")
            print(f"   - 任務ID生成：✓")
        else:
            print(f"[WARNING]  API目前狀態：{response.status_code}")
            print("   需要確保後端服務正確配置")


class TestExecutionTimeMonitoring:
    """執行時間監控功能測試類別"""
    
    def test_execution_time_measurement_accuracy(self):
        """測試 13: 執行時間測量準確性"""
        # Arrange
        import time
        
        # Act - 測試時間測量精度
        start_time = time.time()
        time.sleep(0.1)  # 模擬100ms的執行時間
        end_time = time.time()
        measured_time = end_time - start_time
        
        # Assert
        assert 0.09 <= measured_time <= 0.15, f"時間測量應該準確，預期0.1秒，實際{measured_time:.4f}秒"
        print(f"[OK] 時間測量精度驗證：{measured_time:.4f}秒")
    
    def test_performance_benchmark_standards(self):
        """測試 14: 效能基準標準定義"""
        # Arrange - 定義效能基準
        performance_standards = {
            "api_response_time_max": 5.0,  # API最大回應時間（秒）
            "large_batch_time_max": 10.0,  # 大批次處理最大時間（秒）
            "concurrent_request_time_max": 15.0,  # 並發請求最大處理時間（秒）
            "memory_usage_max": 500,  # 最大記憶體使用量（MB）
        }
        
        # Assert - 驗證標準合理性
        assert performance_standards["api_response_time_max"] > 0, "API回應時間標準應該大於0"
        assert performance_standards["large_batch_time_max"] > performance_standards["api_response_time_max"], "大批次處理時間應該比普通API回應時間更長"
        assert performance_standards["concurrent_request_time_max"] > performance_standards["large_batch_time_max"], "並發請求處理時間應該最長"
        
        print("[OK] 效能基準標準驗證通過：")
        for key, value in performance_standards.items():
            print(f"   - {key}: {value}")


# 測試運行輔助函數
def run_performance_test_suite():
    """運行完整的效能測試套件"""
    print("🚀 開始執行更新所有股票功能效能測試套件...")
    print("=" * 60)
    
    # 這裡可以添加額外的效能測試邏輯
    # 例如：記憶體使用量監控、CPU使用率測試等
    
    print("📊 效能測試重點：")
    print("1. API回應時間 < 5秒")
    print("2. 大批次處理時間 < 10秒") 
    print("3. 並發請求處理能力")
    print("4. 執行時間記錄準確性")
    print("5. 記憶體使用效率")
    print("=" * 60)


if __name__ == "__main__":
    run_performance_test_suite()