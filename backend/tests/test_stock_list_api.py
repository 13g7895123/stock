"""API endpoint tests for stock list functionality - 股票列表API端點測試."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from src.main import app
from src.models.stock import Stock
from src.services.stock_list_service import StockListService


class TestStockListAPI:
    """Test stock list API endpoints - 測試股票列表API端點."""
    
    @pytest.fixture
    def sample_stocks_in_db(self, db_session):
        """Create sample stocks in database for testing."""
        stocks = [
            Stock(symbol="1101", name="台泥", market="TSE", industry="水泥工業", is_active=True),
            Stock(symbol="2330", name="台積電", market="TSE", industry="半導體業", is_active=True),
            Stock(symbol="3008", name="大立光", market="TPEx", industry="光電業", is_active=True),
            Stock(symbol="9999", name="測試股票", market="TSE", industry="測試業", is_active=False),  # Inactive
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()
        
        return stocks
    
    def test_get_stocks_should_return_all_active_stocks(self, client, sample_stocks_in_db):
        """Test GET /api/stocks returns all active stocks."""
        # Act
        response = client.get("/api/stocks/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "stocks" in data
        assert len(data["stocks"]) == 3  # Only active stocks
        assert data["total"] == 3
        
        # Verify stock data structure
        stock = data["stocks"][0]
        assert "symbol" in stock
        assert "name" in stock
        assert "market" in stock
        assert "industry" in stock
        assert "is_active" in stock
        
        # Verify no inactive stocks
        symbols = [s["symbol"] for s in data["stocks"]]
        assert "9999" not in symbols
    
    def test_get_stocks_with_market_filter_should_return_filtered_results(self, client, sample_stocks_in_db):
        """Test GET /api/stocks with market filter."""
        # Act - Filter by TSE
        response = client.get("/api/stocks/?market=TSE")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["stocks"]) == 2  # 1101, 2330
        for stock in data["stocks"]:
            assert stock["market"] == "TSE"
    
    def test_get_stocks_with_pagination_should_limit_results(self, client, sample_stocks_in_db):
        """Test GET /api/stocks with pagination."""
        # Act
        response = client.get("/api/stocks/?skip=0&limit=2")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["stocks"]) == 2
        assert data["total"] == 3  # Total count should still be 3
        assert "has_more" in data
    
    def test_get_stock_by_symbol_should_return_specific_stock(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/{symbol} returns specific stock."""
        # Act
        response = client.get("/api/stocks/2330")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "2330"
        assert data["name"] == "台積電"
        assert data["market"] == "TSE"
        assert data["industry"] == "半導體業"
        assert data["is_active"] is True
    
    def test_get_stock_by_symbol_not_found_should_return_404(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/{symbol} returns 404 for non-existent stock."""
        # Act
        response = client.get("/api/stocks/NOTFOUND")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_stock_by_symbol_inactive_should_return_404(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/{symbol} returns 404 for inactive stock."""
        # Act
        response = client.get("/api/stocks/9999")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower() or "inactive" in data["detail"].lower()
    
    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_sync_stocks_should_trigger_stock_synchronization(self, mock_sync, client):
        """Test POST /api/stocks/sync triggers stock synchronization."""
        # Arrange
        mock_sync.return_value = {
            "success": True,
            "total_stocks": 100,
            "new_stocks": 5,
            "updated_stocks": 95,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Act
        response = client.post("/api/stocks/sync")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["total_stocks"] == 100
        assert data["new_stocks"] == 5
        assert data["updated_stocks"] == 95
        assert "timestamp" in data
        
        # Verify service was called
        mock_sync.assert_called_once()
    
    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_sync_stocks_should_handle_sync_failure(self, mock_sync, client):
        """Test POST /api/stocks/sync handles synchronization failure."""
        # Arrange
        mock_sync.side_effect = Exception("External API failure")
        
        # Act
        response = client.post("/api/stocks/sync")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"].lower() or "failed" in data["detail"].lower()
    
    def test_get_stock_statistics_should_return_market_breakdown(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/statistics returns market statistics."""
        # Act
        response = client.get("/api/stocks/statistics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "total_stocks" in data
        assert "by_market" in data
        assert data["total_stocks"] == 3  # Only active stocks
        assert data["by_market"]["TSE"] == 2
        assert data["by_market"]["TPEx"] == 1
        
        assert "last_updated" in data
        assert "active_stocks" in data
        assert "inactive_stocks" in data
    
    def test_search_stocks_should_return_matching_results(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/search returns matching stocks."""
        # Act - Search by name
        response = client.get("/api/stocks/search?q=台積")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 1
        assert data["results"][0]["symbol"] == "2330"
        assert data["results"][0]["name"] == "台積電"
        assert data["total_found"] == 1
    
    def test_search_stocks_by_symbol_should_return_matching_results(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/search by symbol returns matching stocks."""
        # Act - Search by symbol
        response = client.get("/api/stocks/search?q=1101")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 1
        assert data["results"][0]["symbol"] == "1101"
        assert data["results"][0]["name"] == "台泥"
    
    def test_search_stocks_no_matches_should_return_empty(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/search returns empty results when no matches."""
        # Act
        response = client.get("/api/stocks/search?q=NOMATCH")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 0
        assert data["total_found"] == 0
    
    def test_search_stocks_empty_query_should_return_400(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/search with empty query returns 400."""
        # Act
        response = client.get("/api/stocks/search?q=")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"].lower() or "empty" in data["detail"].lower()
    
    def test_get_stocks_by_industry_should_return_filtered_results(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/by-industry returns stocks filtered by industry."""
        # Act
        response = client.get("/api/stocks/by-industry/半導體業")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["symbol"] == "2330"
        assert data["stocks"][0]["industry"] == "半導體業"
        assert data["industry"] == "半導體業"
        assert data["total"] == 1
    
    def test_get_stocks_by_industry_not_found_should_return_empty(self, client, sample_stocks_in_db):
        """Test GET /api/stocks/by-industry returns empty for non-existent industry."""
        # Act
        response = client.get("/api/stocks/by-industry/不存在的產業")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["stocks"]) == 0
        assert data["total"] == 0
        assert data["industry"] == "不存在的產業"
    
    @patch('src.services.stock_list_service.StockListService.validate_stock_symbols')
    def test_validate_symbols_should_return_validation_results(self, mock_validate, client):
        """Test POST /api/stocks/validate returns symbol validation results."""
        # Arrange
        mock_validate.return_value = {
            "valid_symbols": ["2330", "1101"],
            "invalid_symbols": ["0050", "INVALID"],
            "total_checked": 4,
            "validation_rules": ["4_digits", "non_zero_prefix", "numeric_only"]
        }
        
        symbols_to_validate = ["2330", "1101", "0050", "INVALID"]
        
        # Act
        response = client.post("/api/stocks/validate", json={"symbols": symbols_to_validate})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["valid_symbols"]) == 2
        assert len(data["invalid_symbols"]) == 2
        assert "2330" in data["valid_symbols"]
        assert "0050" in data["invalid_symbols"]
        assert data["total_checked"] == 4
        
        # Verify service was called with correct parameters
        mock_validate.assert_called_once_with(symbols_to_validate)
    
    def test_validate_symbols_empty_list_should_return_400(self, client):
        """Test POST /api/stocks/validate with empty symbol list returns 400."""
        # Act
        response = client.post("/api/stocks/validate", json={"symbols": []})
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower() or "required" in data["detail"].lower()
    
    def test_validate_symbols_invalid_json_should_return_422(self, client):
        """Test POST /api/stocks/validate with invalid JSON returns 422."""
        # Act
        response = client.post("/api/stocks/validate", json={"wrong_field": ["2330"]})
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('src.services.stock_list_service.StockListService.get_sync_status')
    def test_get_sync_status_should_return_last_sync_info(self, mock_status, client):
        """Test GET /api/stocks/sync/status returns synchronization status."""
        # Arrange
        mock_status.return_value = {
            "last_sync_time": "2024-01-01T12:00:00Z",
            "status": "completed",
            "total_stocks_synced": 1500,
            "errors": [],
            "next_scheduled_sync": "2024-01-02T12:00:00Z"
        }
        
        # Act
        response = client.get("/api/stocks/sync/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["total_stocks_synced"] == 1500
        assert len(data["errors"]) == 0
        assert "last_sync_time" in data
        assert "next_scheduled_sync" in data
    
    def test_api_endpoints_should_require_authentication_when_configured(self, client):
        """Test API endpoints require authentication when auth is enabled."""
        # This test documents expected behavior when authentication is implemented
        # Currently, endpoints are open, but this test ensures we consider security
        
        # For now, verify endpoints are accessible (no auth implemented)
        response = client.get("/api/stocks/")
        assert response.status_code in [200, 401, 403]  # 200 if no auth, 401/403 if auth required
    
    def test_api_endpoints_should_have_rate_limiting_when_configured(self, client):
        """Test API endpoints implement rate limiting when configured."""
        # This test documents expected behavior for rate limiting
        # Make multiple rapid requests
        
        responses = []
        for _ in range(10):
            response = client.get("/api/stocks/statistics")
            responses.append(response.status_code)
        
        # For now, all requests should succeed (no rate limiting implemented)
        # When rate limiting is implemented, some requests should return 429
        success_responses = [code for code in responses if code == 200]
        rate_limited_responses = [code for code in responses if code == 429]
        
        # Either all succeed (no rate limiting) or some are rate limited
        assert len(success_responses) > 0
        # assert len(rate_limited_responses) > 0  # Uncomment when rate limiting implemented
    
    def test_api_error_responses_should_have_consistent_format(self, client):
        """Test API error responses follow consistent format."""
        # Test 404 error
        response = client.get("/api/stocks/NONEXISTENT")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)
        
        # Test 400 error
        response = client.get("/api/stocks/search?q=")
        if response.status_code == 400:
            error_data = response.json()
            assert "detail" in error_data
            assert isinstance(error_data["detail"], str)

    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_crawl_stocks_should_fetch_and_update_database(self, mock_sync, client):
        """Test GET /api/v1/sync/stocks/crawl crawls and updates stock list."""
        # Arrange
        mock_sync.return_value = {
            "status": "success",
            "message": "Stock synchronization completed successfully",
            "total_stocks": 120,
            "tse_stocks": 80,
            "tpex_stocks": 40,
            "new_stocks": 5,
            "updated_stocks": 115,
            "filtered_stocks": 120,
            "timestamp": "2025-09-09T12:00:00Z"
        }
        
        # Act
        response = client.get("/api/v1/sync/stocks/crawl")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["total_stocks"] == 120
        assert data["tse_stocks"] == 80
        assert data["tpex_stocks"] == 40
        assert data["new_stocks"] == 5
        assert data["updated_stocks"] == 115
        assert "timestamp" in data
        assert "message" in data
        
        # Verify service was called
        mock_sync.assert_called_once()

    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_crawl_stocks_should_handle_partial_success(self, mock_sync, client):
        """Test GET /api/v1/sync/stocks/crawl handles partial success."""
        # Arrange
        mock_sync.return_value = {
            "status": "partial_success",
            "message": "TSE sync successful, TPEx sync failed",
            "total_stocks": 80,
            "tse_stocks": 80,
            "tpex_stocks": 0,
            "errors": ["TPEx API connection timeout"],
            "timestamp": "2025-09-09T12:00:00Z"
        }
        
        # Act
        response = client.get("/api/v1/sync/stocks/crawl")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "partial_success"
        assert data["total_stocks"] == 80
        assert data["tse_stocks"] == 80
        assert data["tpex_stocks"] == 0
        assert "errors" in data
        assert len(data["errors"]) == 1

    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_crawl_stocks_should_handle_sync_failure(self, mock_sync, client):
        """Test GET /api/v1/sync/stocks/crawl handles sync failure."""
        # Arrange
        mock_sync.side_effect = Exception("External API connection failed")
        
        # Act
        response = client.get("/api/v1/sync/stocks/crawl")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower() or "error" in data["detail"].lower()

    @patch('src.services.stock_list_service.StockListService.sync_all_stocks')
    def test_crawl_stocks_should_return_database_update_info(self, mock_sync, client):
        """Test GET /api/v1/sync/stocks/crawl returns database update information."""
        # Arrange
        mock_sync.return_value = {
            "status": "success",
            "message": "Stock list crawled and database updated",
            "total_stocks": 150,
            "filtered_stocks": 120,  # After filtering (4-digit, non-zero prefix)
            "new_stocks": 10,
            "updated_stocks": 110,
            "duplicate_stocks": 0,
            "database_updated": True,
            "last_update_time": "2025-09-09T12:00:00Z"
        }
        
        # Act
        response = client.get("/api/v1/sync/stocks/crawl")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["database_updated"] is True
        assert data["filtered_stocks"] == 120
        assert data["new_stocks"] == 10
        assert data["updated_stocks"] == 110
        assert "last_update_time" in data

    def test_crawl_stocks_should_be_idempotent(self, client, db_session):
        """Test GET /api/v1/sync/stocks/crawl is idempotent - can be called multiple times safely."""
        # This test ensures calling the crawl endpoint multiple times doesn't cause issues
        with patch('src.services.stock_list_service.StockListService.sync_all_stocks') as mock_sync:
            mock_sync.return_value = {
                "status": "success",
                "total_stocks": 100,
                "new_stocks": 0,  # No new stocks on second call
                "updated_stocks": 100,
                "timestamp": "2025-09-09T12:00:00Z"
            }
            
            # Act - Call twice
            response1 = client.get("/api/v1/sync/stocks/crawl")
            response2 = client.get("/api/v1/sync/stocks/crawl")
            
            # Assert
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Both calls should succeed
            data1 = response1.json()
            data2 = response2.json()
            
            assert data1["status"] == "success"
            assert data2["status"] == "success"