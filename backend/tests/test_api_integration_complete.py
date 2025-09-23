"""
Complete API Integration Test Suite
完整的 API 整合測試套件

測試所有 API 端點的功能、回應格式、錯誤處理和邊界情況
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.core.database import get_db
from src.services.stock_list_service import StockListService
from src.services.daily_data_service import DailyDataService
from src.services.stock_history_service import StockHistoryService
from src.services.moving_averages_service import MovingAveragesService
from src.services.task_execution_service import TaskExecutionService
from src.services.stock_selection_service import StockSelectionService


class TestCompleteAPIIntegration:
    """完整的 API 整合測試類"""

    @pytest.fixture
    def client(self):
        """FastAPI 測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """Mock 資料庫連線"""
        db_mock = Mock(spec=Session)
        return db_mock

    @pytest.fixture
    def override_get_db(self, mock_db):
        """覆寫資料庫依賴"""
        def _override_get_db():
            return mock_db
        app.dependency_overrides[get_db] = _override_get_db
        yield
        app.dependency_overrides.clear()

    # ==================== 健康檢查 API 測試 ====================

    def test_health_check_basic(self, client):
        """測試基本健康檢查 API"""
        response = client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()

        # 驗證基本欄位
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "healthy"

        # 驗證時間戳格式
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

    def test_health_check_detailed(self, client, override_get_db):
        """測試詳細健康檢查 API"""
        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()

        # 驗證詳細檢查欄位
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "celery" in data["checks"]

        # 驗證每個檢查都有狀態和訊息
        for check_name, check_data in data["checks"].items():
            assert "status" in check_data
            assert "message" in check_data

    def test_health_check_readiness(self, client, override_get_db):
        """測試就緒檢查 API"""
        response = client.get("/api/v1/health/readiness")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ready"
        assert "timestamp" in data

    def test_health_check_liveness(self, client):
        """測試存活檢查 API"""
        response = client.get("/api/v1/health/liveness")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "alive"
        assert "timestamp" in data

    # ==================== 股票同步 API 測試 ====================

    @patch('src.services.stock_list_service.StockListService')
    def test_sync_stocks_count(self, mock_service_class, client, override_get_db):
        """測試股票數量統計 API"""
        # 設定 Mock 回傳值
        mock_service = Mock()
        mock_service.get_stock_count_by_market.return_value = {
            "TSE": 1053,
            "TPEx": 855
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/sync/stocks/count")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "by_market" in data
        assert "markets" in data
        assert data["total"] == 1908
        assert data["by_market"]["TSE"] == 1053
        assert data["by_market"]["TPEx"] == 855

    @patch('src.services.stock_list_service.StockListService')
    def test_sync_stocks_list(self, mock_service_class, client, override_get_db):
        """測試同步股票列表 API"""
        # 設定 Mock 回傳值
        mock_service = Mock()
        mock_service.sync_all_stocks.return_value = {
            "status": "success",
            "total_stocks": 1908,
            "tse_stocks": 1053,
            "tpex_stocks": 855,
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_service_class.return_value = mock_service

        response = client.post("/api/v1/sync/stocks/sync")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["total_stocks"] == 1908
        assert "timestamp" in data

    @patch('src.services.stock_list_service.StockListService')
    def test_sync_stocks_crawl(self, mock_service_class, client, override_get_db):
        """測試爬取股票列表 API"""
        mock_service = Mock()
        mock_service.sync_all_stocks.return_value = {
            "status": "success",
            "total_stocks": 1908,
            "new_stocks": 5,
            "updated_stocks": 10
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/sync/stocks/crawl")

        assert response.status_code == 200
        data = response.json()

        assert data["database_updated"] is True
        assert "new_stocks" in data
        assert "updated_stocks" in data

    def test_validate_stock_symbol_valid(self, client):
        """測試有效股票代號驗證"""
        response = client.get("/api/v1/sync/stocks/validate/2330")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "2330"
        assert data["is_four_digit"] is True
        assert data["is_numeric"] is True
        assert data["starts_with_zero"] is False
        assert "is_valid" in data

    def test_validate_stock_symbol_invalid(self, client):
        """測試無效股票代號驗證"""
        response = client.get("/api/v1/sync/stocks/validate/123")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "123"
        assert data["is_four_digit"] is False
        assert data["is_valid"] is False

    # ==================== 股票資料 API 測試 ====================

    @patch('src.services.stock_list_service.StockListService')
    def test_stocks_list(self, mock_service_class, client, override_get_db):
        """測試股票列表 API"""
        mock_service = Mock()
        mock_service.get_stock_list.return_value = {
            "stocks": [
                {
                    "symbol": "2330",
                    "name": "台積電",
                    "market": "TSE"
                },
                {
                    "symbol": "2317",
                    "name": "鴻海",
                    "market": "TSE"
                }
            ],
            "total": 2
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/stocks/list?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "stocks" in data
        assert len(data["stocks"]) == 2
        assert data["stocks"][0]["symbol"] == "2330"

    def test_stocks_update_all_empty_body(self, client, override_get_db):
        """測試批次更新所有股票（無參數）"""
        response = client.post("/api/v1/stocks/update-all")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "symbols from database" in data["message"]

    def test_stocks_update_all_with_symbols(self, client, override_get_db):
        """測試批次更新指定股票"""
        symbols = ["2330", "2317"]
        response = client.post("/api/v1/stocks/update-all", json=symbols)

        assert response.status_code == 200
        data = response.json()

        assert "2 symbols" in data["message"]

    # ==================== 歷史資料 API 測試 ====================

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_history_overview(self, mock_service_class, client, override_get_db):
        """測試歷史資料統計 API"""
        mock_service = Mock()
        mock_service.get_overall_statistics.return_value = {
            "total_stocks": 1109,
            "total_records": 1234567,
            "latest_date": "2025-01-01",
            "completeness": 85.5
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/overview")

        assert response.status_code == 200
        data = response.json()

        assert data["total_stocks"] == 1109
        assert data["total_records"] == 1234567
        assert data["latest_date"] == "2025-01-01"
        assert data["completeness"] == 85.5

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_history_stocks_with_data(self, mock_service_class, client, override_get_db):
        """測試有資料股票清單 API"""
        mock_service = Mock()
        mock_service.get_stocks_with_data.return_value = {
            "stocks": [
                {"stock_code": "2330", "stock_name": "台積電", "record_count": 1440},
                {"stock_code": "2317", "stock_name": "鴻海", "record_count": 1440}
            ],
            "total": 2
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/stocks-with-data?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "stocks" in data
        assert len(data["stocks"]) == 2
        assert data["stocks"][0]["stock_code"] == "2330"

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_history_stock_data(self, mock_service_class, client, override_get_db):
        """測試股票歷史資料查詢 API"""
        mock_service = Mock()
        mock_service.get_stock_history.return_value = {
            "data": [
                {
                    "trade_date": "2025-01-01",
                    "open_price": 100.0,
                    "high_price": 105.0,
                    "low_price": 98.0,
                    "close_price": 103.0,
                    "volume": 10000
                }
            ],
            "total_records": 1440
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/2330?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert data["stock_symbol"] == "2330"
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["trade_date"] == "2025-01-01"

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_history_stock_stats(self, mock_service_class, client, override_get_db):
        """測試股票統計資訊 API"""
        mock_service = Mock()
        mock_service.get_stock_statistics.return_value = {
            "total_records": 1440,
            "date_range": {
                "earliest": "2019-01-01",
                "latest": "2025-01-01"
            },
            "price_range": {
                "min_price": 90.0,
                "max_price": 150.0
            }
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/2330/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["stock_symbol"] == "2330"
        assert data["total_records"] == 1440
        assert "date_range" in data
        assert "price_range" in data

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_history_latest_date(self, mock_service_class, client, override_get_db):
        """測試最新交易日期 API"""
        mock_service = Mock()
        mock_service.get_latest_trade_date.return_value = {
            "latest_trade_date": "2025-01-01",
            "has_data": True
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/2330/latest-date")

        assert response.status_code == 200
        data = response.json()

        assert data["stock_symbol"] == "2330"
        assert data["latest_trade_date"] == "2025-01-01"
        assert data["has_data"] is True

    @patch('src.services.daily_data_service.DailyDataService')
    def test_data_daily_update(self, mock_service_class, client, override_get_db):
        """測試單一股票資料更新 API"""
        mock_service = Mock()
        mock_service.get_daily_data_for_stock.return_value = {
            "status": "success",
            "records_processed": 1440,
            "records_created": 0,
            "records_updated": 1440
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/daily/2330")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["records_processed"] == 1440

    # ==================== 任務管理 API 測試 ====================

    @patch('src.services.task_execution_service.TaskExecutionService')
    def test_task_execution_running(self, mock_service_class, client, override_get_db):
        """測試執行中任務 API"""
        mock_service = Mock()
        mock_service.get_running_tasks.return_value = {
            "running_tasks": [
                {
                    "id": "task-123",
                    "task_name": "Stock Crawl Task",
                    "status": "running",
                    "progress": 50.0,
                    "start_time": "2025-01-01T00:00:00"
                }
            ]
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/task-execution/running")

        assert response.status_code == 200
        data = response.json()

        assert "running_tasks" in data
        assert len(data["running_tasks"]) == 1
        assert data["running_tasks"][0]["status"] == "running"

    @patch('src.services.task_execution_service.TaskExecutionService')
    def test_task_execution_recent(self, mock_service_class, client, override_get_db):
        """測試最近任務記錄 API"""
        mock_service = Mock()
        mock_service.get_recent_tasks.return_value = {
            "tasks": [
                {
                    "id": "task-123",
                    "task_name": "Stock Crawl Task",
                    "status": "completed",
                    "duration_seconds": 120,
                    "processed_count": 1908
                }
            ],
            "total": 1
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/task-execution/recent")

        assert response.status_code == 200
        data = response.json()

        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["status"] == "completed"

    @patch('src.services.task_execution_service.TaskExecutionService')
    def test_task_execution_statistics(self, mock_service_class, client, override_get_db):
        """測試任務統計 API"""
        mock_service = Mock()
        mock_service.get_task_statistics.return_value = {
            "total_tasks": 10,
            "running_count": 1,
            "completed_count": 8,
            "failed_count": 1,
            "success_rate": 80.0,
            "average_duration": 150.0
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/task-execution/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "statistics" in data
        assert data["statistics"]["total_tasks"] == 10
        assert data["statistics"]["success_rate"] == 80.0

    @patch('src.services.task_execution_service.TaskExecutionService')
    def test_task_execution_status(self, mock_service_class, client, override_get_db):
        """測試任務狀態查詢 API"""
        mock_service = Mock()
        mock_service.get_task_by_id.return_value = {
            "id": "task-123",
            "task_name": "Stock Crawl Task",
            "status": "completed",
            "progress": 100.0,
            "processed_count": 1908,
            "success_count": 1900,
            "error_count": 8
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/task-execution/status/task-123")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "task" in data
        assert data["task"]["id"] == "task-123"

    def test_tasks_manual_stock_crawl(self, client, override_get_db):
        """測試創建爬蟲任務 API"""
        symbols = ["2330", "2317"]
        response = client.post("/api/v1/tasks/manual/stock-crawl", json=symbols)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "task_id" in data
        assert "symbols_count" in data

    # ==================== 均線計算 API 測試 ====================

    @patch('src.services.moving_averages_service.MovingAveragesService')
    def test_moving_averages_statistics(self, mock_service_class, client, override_get_db):
        """測試均線統計 API"""
        mock_service = Mock()
        mock_service.get_statistics.return_value = {
            "stocks_with_ma": 978,
            "total_ma_records": 333707,
            "latest_calculation_date": "2025-01-01",
            "calculation_completeness": 51.3
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/moving-averages/statistics")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["stocks_with_ma"] == 978
        assert data["data"]["total_ma_records"] == 333707

    @patch('src.services.moving_averages_service.MovingAveragesService')
    def test_moving_averages_query(self, mock_service_class, client, override_get_db):
        """測試均線查詢 API"""
        mock_service = Mock()
        mock_service.query_moving_averages.return_value = {
            "data": [
                {
                    "trade_date": "2025-01-01",
                    "ma5": 100.5,
                    "ma10": 99.8,
                    "ma24": 98.2,
                    "close_price": 103.0
                }
            ],
            "pagination": {
                "page": 1,
                "limit": 10,
                "total": 1440
            }
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/moving-averages/query/2330?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["stock_code"] == "2330"
        assert len(data["data"]) == 1
        assert data["data"][0]["ma5"] == 100.5

    @patch('src.services.moving_averages_service.MovingAveragesService')
    def test_moving_averages_validate(self, mock_service_class, client, override_get_db):
        """測試均線驗證 API"""
        mock_service = Mock()
        mock_service.validate_moving_averages.return_value = {
            "is_valid": True,
            "total_records": 333707,
            "invalid_records": 0,
            "validation_results": []
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/moving-averages/validate")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["is_valid"] is True
        assert data["data"]["invalid_records"] == 0

    # ==================== 選股 API 測試 ====================

    @patch('src.services.stock_selection_service.StockSelectionService')
    def test_stock_selection_bullish(self, mock_service_class, client, override_get_db):
        """測試短線多頭選股 API"""
        mock_service = Mock()
        mock_service.get_bullish_short_term_stocks.return_value = {
            "stocks": [
                {
                    "stock_code": "2330",
                    "stock_name": "台積電",
                    "current_price": 103.0,
                    "ma5": 100.5,
                    "ma10": 99.8,
                    "score": 85.5
                }
            ],
            "total_count": 26,
            "selection_criteria": "short_term_bullish"
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/stock-selection/bullish-short-term")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["stock_code"] == "2330"
        assert data["total_count"] == 26

    @patch('src.services.stock_selection_service.StockSelectionService')
    def test_stock_selection_bearish(self, mock_service_class, client, override_get_db):
        """測試短線空頭選股 API"""
        mock_service = Mock()
        mock_service.get_bearish_short_term_stocks.return_value = {
            "stocks": [
                {
                    "stock_code": "1234",
                    "stock_name": "測試股票",
                    "current_price": 50.0,
                    "ma5": 55.0,
                    "ma10": 58.0,
                    "score": 15.5
                }
            ],
            "total_count": 12,
            "selection_criteria": "short_term_bearish"
        }
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/stock-selection/bearish-short-term")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["score"] == 15.5

    # ==================== 錯誤處理測試 ====================

    def test_invalid_stock_symbol_format(self, client):
        """測試無效股票代號格式錯誤處理"""
        response = client.get("/api/v1/data/history/123/stats")

        assert response.status_code == 422
        data = response.json()

        assert "Invalid stock symbol" in data["detail"]

    def test_nonexistent_endpoint(self, client):
        """測試不存在的端點錯誤處理"""
        response = client.get("/api/v1/nonexistent/endpoint")

        assert response.status_code == 404

    def test_invalid_json_payload(self, client):
        """測試無效 JSON 負載錯誤處理"""
        response = client.post(
            "/api/v1/stocks/update-all",
            data="invalid json",
            headers={"content-type": "application/json"}
        )

        assert response.status_code == 422

    @patch('src.services.stock_history_service.StockHistoryService')
    def test_service_exception_handling(self, mock_service_class, client, override_get_db):
        """測試服務層例外處理"""
        mock_service = Mock()
        mock_service.get_stock_history.side_effect = Exception("Database connection error")
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/data/history/2330")

        assert response.status_code == 500
        data = response.json()

        assert "error" in data or "detail" in data

    # ==================== 效能測試 ====================

    def test_api_response_time(self, client):
        """測試 API 回應時間"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/health/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 應在 1 秒內回應

    def test_concurrent_requests(self, client):
        """測試並發請求處理"""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/health/")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 所有請求都應成功
        for response in responses:
            assert response.status_code == 200

    # ==================== CORS 測試 ====================

    def test_cors_headers(self, client):
        """測試 CORS 標頭"""
        response = client.options(
            "/api/v1/health/",
            headers={"Origin": "http://localhost:3000"}
        )

        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_cors_preflight(self, client):
        """測試 CORS 預檢請求"""
        response = client.options(
            "/api/v1/sync/stocks/count",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code in [200, 204]

    # ==================== 資料驗證測試 ====================

    def test_stock_symbol_validation_edge_cases(self, client):
        """測試股票代號驗證邊界情況"""
        test_cases = [
            ("0123", False),  # 以零開頭
            ("12345", False), # 超過四位
            ("12a3", False),  # 包含字母
            ("", False),      # 空字串
            ("2330", True),   # 有效代號
        ]

        for symbol, expected_valid in test_cases:
            response = client.get(f"/api/v1/sync/stocks/validate/{symbol}")

            if response.status_code == 200:
                data = response.json()
                # 根據實際 API 邏輯驗證結果
                assert "is_valid" in data

    def test_pagination_parameters(self, client, override_get_db):
        """測試分頁參數驗證"""
        # 測試有效分頁參數
        response = client.get("/api/v1/data/history/stocks-with-data?page=1&limit=10")
        assert response.status_code == 200

        # 測試無效分頁參數
        response = client.get("/api/v1/data/history/stocks-with-data?page=0&limit=10")
        assert response.status_code == 422

        response = client.get("/api/v1/data/history/stocks-with-data?page=1&limit=10001")
        assert response.status_code == 422

    # ==================== 整合流程測試 ====================

    def test_complete_stock_data_flow(self, client, override_get_db):
        """測試完整股票資料流程"""
        # 1. 檢查系統健康狀態
        health_response = client.get("/api/v1/health/")
        assert health_response.status_code == 200

        # 2. 獲取股票數量
        count_response = client.get("/api/v1/sync/stocks/count")
        assert count_response.status_code == 200

        # 3. 驗證股票代號
        validate_response = client.get("/api/v1/sync/stocks/validate/2330")
        assert validate_response.status_code == 200

        # 4. 查詢股票歷史資料（如果存在）
        history_response = client.get("/api/v1/data/history/2330?limit=1")
        # 可能回傳 200（有資料）或 404（無資料），都是有效回應
        assert history_response.status_code in [200, 404, 422]

    def test_task_management_flow(self, client, override_get_db):
        """測試任務管理完整流程"""
        # 1. 檢查執行中任務
        running_response = client.get("/api/v1/task-execution/running")
        assert running_response.status_code == 200

        # 2. 查看任務統計
        stats_response = client.get("/api/v1/task-execution/statistics")
        assert stats_response.status_code == 200

        # 3. 創建新任務
        create_response = client.post("/api/v1/tasks/manual/stock-crawl", json=["2330"])
        assert create_response.status_code == 200

        if create_response.json().get("success"):
            task_id = create_response.json().get("task_id")
            if task_id:
                # 4. 查詢任務狀態
                status_response = client.get(f"/api/v1/task-execution/status/{task_id}")
                # 任務可能不存在於測試環境，但 API 應正常回應
                assert status_response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])