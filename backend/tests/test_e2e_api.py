"""End-to-End API Integration Tests.

These tests run against the complete Docker stack:
- PostgreSQL database 
- FastAPI backend service
- Real HTTP requests to running API
- Database verification of API operations

Run these tests against the running Docker services:
- API: http://localhost:8000 (or port configured in docker-compose)
- Database: postgresql://stock_user:password@localhost:5432/stock_analysis

Prerequisites:
1. docker-compose up -d  # Start all services
2. Wait for services to be healthy
3. Run tests: pytest tests/test_e2e_api.py -v
"""
import pytest
import asyncio
import time
from typing import Dict, Any, List
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, Mock

from src.models.stock import Stock


# Test configuration for Docker services
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://stock_user:password@localhost:5432/stock_analysis"

# Test timeout and retry configuration
API_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0


class TestEndToEndAPI:
    """End-to-end API tests with real database verification."""

    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create database engine for verification queries."""
        engine = create_engine(DATABASE_URL, echo=False)
        yield engine
        engine.dispose()

    @pytest.fixture(scope="class")
    def db_session_factory(self, db_engine):
        """Create session factory for database verification."""
        return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    @pytest.fixture
    def db_session(self, db_session_factory):
        """Create database session for test verification."""
        session = db_session_factory()
        yield session
        session.close()

    @pytest.fixture(scope="class")
    def http_client(self):
        """Create HTTP client for API requests."""
        return httpx.Client(
            base_url=API_BASE_URL,
            timeout=API_TIMEOUT,
            follow_redirects=True
        )

    @pytest.fixture
    def clean_test_data(self, db_session):
        """Clean test data before and after each test."""
        self._cleanup_test_stocks(db_session)
        yield
        self._cleanup_test_stocks(db_session)

    def _cleanup_test_stocks(self, db_session):
        """Remove test stocks from database."""
        try:
            # Clean up known test stock symbols
            test_symbols = ['9001', '9002', '9003', '9004', '9005', '1101', '2330', '3008', '4938']
            for symbol in test_symbols:
                db_session.execute(
                    text("DELETE FROM stocks WHERE symbol = :symbol"),
                    {"symbol": symbol}
                )
            db_session.commit()
        except Exception:
            db_session.rollback()

    def _wait_for_api_ready(self, http_client, max_attempts=10):
        """Wait for API to be ready before running tests."""
        for attempt in range(max_attempts):
            try:
                response = http_client.get("/health")
                if response.status_code == 200:
                    return True
                time.sleep(RETRY_DELAY)
            except Exception:
                if attempt < max_attempts - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise
        return False

    def _insert_test_stocks(self, db_session, stocks: List[Dict[str, Any]]):
        """Insert test stocks directly into database."""
        for stock_data in stocks:
            stock = Stock(
                symbol=stock_data["symbol"],
                name=stock_data["name"],
                market=stock_data["market"],
                is_active=True
            )
            db_session.add(stock)
        db_session.commit()

    def test_api_health_check(self, http_client):
        """Test that API health endpoint is accessible."""
        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API should be ready and responsive"
        
        # Test health endpoint
        response = http_client.get("/health")
        
        assert response.status_code == 200, "Health check should return 200"
        health_data = response.json()
        assert health_data.get("status") == "healthy", "API should report healthy status"

    @pytest.mark.asyncio
    async def test_sync_stocks_api_creates_database_records(self, http_client, db_session, clean_test_data):
        """Test POST /api/v1/sync/stocks/sync creates records in database."""
        # Arrange - Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"
        
        # Mock the external API calls to return predictable test data
        mock_tse_response = {
            "stat": "OK",
            "data": [
                ["1101", "台泥"],
                ["2330", "台積電"],
            ]
        }
        
        mock_tpex_response = {
            "stat": "OK", 
            "aaData": [
                ["3008", "大立光"],
                ["4938", "和碩"],
            ]
        }

        # We need to mock at the service level since we're testing E2E
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            # Configure mock responses for TSE and TPEx calls
            mock_responses = []
            
            # TSE response
            tse_response = Mock()
            tse_response.status_code = 200
            tse_response.json.return_value = mock_tse_response
            tse_response.raise_for_status = Mock()
            
            # TPEx response
            tpex_response = Mock()
            tpex_response.status_code = 200
            tpex_response.json.return_value = mock_tpex_response
            tpex_response.raise_for_status = Mock()
            
            mock_instance.get.side_effect = [tse_response, tpex_response]

            # Act - Call sync API
            response = http_client.post("/api/v1/sync/stocks/sync")

            # Assert - API response
            assert response.status_code == 200, f"Sync API should return 200, got {response.status_code}: {response.text}"
            sync_result = response.json()
            
            assert sync_result["status"] == "success", "Sync should report success"
            assert sync_result["total_fetched"] == 4, "Should fetch 4 stocks"
            assert sync_result["created"] == 4, "Should create 4 new stocks"
            assert sync_result["updated"] == 0, "Should not update any stocks initially"

        # Assert - Database verification
        saved_stocks = db_session.query(Stock).filter(
            Stock.symbol.in_(["1101", "2330", "3008", "4938"])
        ).all()
        
        assert len(saved_stocks) == 4, "All synced stocks should be saved in database"
        
        stock_by_symbol = {stock.symbol: stock for stock in saved_stocks}
        assert stock_by_symbol["1101"].name == "台泥"
        assert stock_by_symbol["1101"].market == "TSE"
        assert stock_by_symbol["2330"].name == "台積電"
        assert stock_by_symbol["3008"].market == "TPEx"
        assert stock_by_symbol["4938"].name == "和碩"
        
        # Verify all stocks are active
        for stock in saved_stocks:
            assert stock.is_active is True, f"Stock {stock.symbol} should be active"

    def test_get_stock_counts_api_reads_from_database(self, http_client, db_session, clean_test_data):
        """Test GET /api/v1/sync/stocks/count reads from database."""
        # Arrange - Insert test data directly into database
        test_stocks = [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "3008", "name": "大立光", "market": "TPEx"},
        ]
        self._insert_test_stocks(db_session, test_stocks)

        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        # Act - Call counts API
        response = http_client.get("/api/v1/sync/stocks/count")

        # Assert - API response matches database
        assert response.status_code == 200, f"Counts API should return 200, got {response.status_code}: {response.text}"
        counts_data = response.json()
        
        assert counts_data["total"] == 3, "Total count should match database records"
        assert counts_data["by_market"]["TSE"] == 2, "TSE count should match database"
        assert counts_data["by_market"]["TPEx"] == 1, "TPEx count should match database"
        assert set(counts_data["markets"]) == {"TSE", "TPEx"}, "Markets should match database"

        # Verify database state hasn't changed
        db_count = db_session.query(Stock).filter(
            Stock.symbol.in_(["1101", "2330", "3008"]),
            Stock.is_active == True
        ).count()
        assert db_count == 3, "Database should still contain test stocks"

    def test_data_persistence_across_api_calls(self, http_client, db_session, clean_test_data):
        """Test that data persists across multiple API calls."""
        # Arrange - Insert initial test data
        initial_stocks = [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
        ]
        self._insert_test_stocks(db_session, initial_stocks)

        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        # Act 1 - First API call to get counts
        response1 = http_client.get("/api/v1/sync/stocks/count")
        assert response1.status_code == 200
        counts1 = response1.json()
        
        # Act 2 - Second API call to get counts (should be same)
        response2 = http_client.get("/api/v1/sync/stocks/count")
        assert response2.status_code == 200
        counts2 = response2.json()

        # Assert - Data should persist across calls
        assert counts1 == counts2, "Data should be consistent across API calls"
        assert counts1["total"] == 2, "Should consistently report 2 stocks"

        # Verify database state
        persistent_stocks = db_session.query(Stock).filter(
            Stock.symbol.in_(["1101", "2330"]),
            Stock.is_active == True
        ).all()
        assert len(persistent_stocks) == 2, "Stocks should persist in database"

    def test_sync_api_updates_existing_stocks(self, http_client, db_session, clean_test_data):
        """Test that sync API updates existing stocks in database."""
        # Arrange - Insert existing stock with old name
        existing_stocks = [
            {"symbol": "1101", "name": "台灣水泥", "market": "TSE"},
        ]
        self._insert_test_stocks(db_session, existing_stocks)

        # Mock API to return updated name
        mock_tse_response = {
            "stat": "OK",
            "data": [
                ["1101", "台泥"],  # Updated name
                ["2330", "台積電"],  # New stock
            ]
        }
        
        mock_tpex_response = {
            "stat": "OK",
            "aaData": []  # No TPEx stocks
        }

        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            tse_response = Mock()
            tse_response.status_code = 200
            tse_response.json.return_value = mock_tse_response
            tse_response.raise_for_status = Mock()
            
            tpex_response = Mock()
            tpex_response.status_code = 200
            tpex_response.json.return_value = mock_tpex_response
            tpex_response.raise_for_status = Mock()
            
            mock_instance.get.side_effect = [tse_response, tpex_response]

            # Act - Call sync API
            response = http_client.post("/api/v1/sync/stocks/sync")

            # Assert - API response
            assert response.status_code == 200
            sync_result = response.json()
            
            assert sync_result["status"] == "success"
            assert sync_result["created"] == 1, "Should create 1 new stock (2330)"
            assert sync_result["updated"] == 1, "Should update 1 existing stock (1101)"

        # Assert - Database verification
        updated_stock = db_session.query(Stock).filter_by(symbol="1101").first()
        new_stock = db_session.query(Stock).filter_by(symbol="2330").first()
        
        assert updated_stock is not None, "Existing stock should still exist"
        assert updated_stock.name == "台泥", "Existing stock name should be updated"
        assert updated_stock.market == "TSE", "Market should remain unchanged"
        
        assert new_stock is not None, "New stock should be created"
        assert new_stock.name == "台積電"

    def test_api_error_handling_with_database_rollback(self, http_client, db_session, clean_test_data):
        """Test API error handling and database rollback behavior."""
        # Arrange - Insert test stock to verify rollback
        initial_count = db_session.query(Stock).count()
        
        # Mock API to simulate external service failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            # Simulate API failure
            error_response = Mock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock()
            )
            mock_instance.get.return_value = error_response

            # Ensure API is ready
            assert self._wait_for_api_ready(http_client), "API must be ready"

            # Act - Call sync API (should fail)
            response = http_client.post("/api/v1/sync/stocks/sync")

            # Assert - API should return error
            assert response.status_code == 500, "API should return error status"
            error_data = response.json()
            assert "error" in error_data.get("detail", "").lower(), "Should contain error message"

        # Assert - Database should be unchanged (rollback)
        final_count = db_session.query(Stock).count()
        assert final_count == initial_count, "Database should be unchanged after API error"

    def test_validate_stock_symbol_api(self, http_client):
        """Test stock symbol validation API endpoint."""
        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        test_cases = [
            ("1101", True, "Valid 4-digit non-zero-prefix symbol"),
            ("2330", True, "Valid 4-digit non-zero-prefix symbol"), 
            ("0050", False, "Invalid zero-prefix symbol"),
            ("ABCD", False, "Invalid non-numeric symbol"),
            ("12345", False, "Invalid 5-digit symbol"),
            ("123", False, "Invalid 3-digit symbol"),
        ]

        for symbol, expected_valid, description in test_cases:
            # Act
            response = http_client.get(f"/api/v1/sync/stocks/validate/{symbol}")
            
            # Assert
            assert response.status_code == 200, f"Validation API should return 200 for {symbol}"
            validation_data = response.json()
            
            assert validation_data["symbol"] == symbol, f"Should return tested symbol"
            assert validation_data["is_valid"] == expected_valid, f"{description}: {symbol}"
            assert validation_data["is_four_digit"] == (len(symbol) == 4), f"Length check for {symbol}"
            assert validation_data["is_numeric"] == symbol.isdigit(), f"Numeric check for {symbol}"

    def test_concurrent_api_requests(self, http_client, db_session, clean_test_data):
        """Test concurrent API requests with database consistency."""
        import threading
        import queue
        
        # Arrange - Insert base data
        base_stocks = [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
        ]
        self._insert_test_stocks(db_session, base_stocks)
        
        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        results_queue = queue.Queue()
        
        def make_api_call():
            """Make API call in separate thread."""
            try:
                response = http_client.get("/api/v1/sync/stocks/count")
                results_queue.put((response.status_code, response.json()))
            except Exception as e:
                results_queue.put((500, {"error": str(e)}))

        # Act - Make concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_api_call)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout

        # Assert - All requests should succeed with consistent data
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == 3, "All concurrent requests should complete"
        
        for status_code, data in results:
            assert status_code == 200, "All concurrent requests should succeed"
            assert data["total"] == 1, "All requests should return consistent data"
            assert data["by_market"]["TSE"] == 1, "Market counts should be consistent"

    def test_api_performance_benchmarks(self, http_client, db_session, clean_test_data):
        """Test API response times within acceptable limits."""
        # Arrange - Insert moderate dataset
        perf_stocks = []
        for i in range(9100, 9150):  # 50 stocks for performance test
            perf_stocks.append({
                "symbol": str(i),
                "name": f"性能測試股票{i}",
                "market": "TSE" if i % 2 == 0 else "TPEx"
            })
        self._insert_test_stocks(db_session, perf_stocks)

        # Ensure API is ready
        assert self._wait_for_api_ready(http_client), "API must be ready"

        # Act & Assert - Test response times
        start_time = time.time()
        response = http_client.get("/api/v1/sync/stocks/count")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200, "Performance test API call should succeed"
        assert response_time < 2.0, f"API should respond within 2 seconds, took {response_time:.2f}s"
        
        # Verify data correctness
        data = response.json()
        assert data["total"] >= 50, "Should include performance test stocks"


class TestAPIServiceIntegration:
    """Test integration between API endpoints and service layer."""

    @pytest.fixture
    def http_client(self):
        """Create HTTP client for API requests."""
        return httpx.Client(base_url=API_BASE_URL, timeout=API_TIMEOUT)

    def test_api_service_error_propagation(self, http_client):
        """Test that service layer errors are properly handled by API."""
        # Mock service to raise exception
        with patch('src.services.stock_list_service.StockListService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.get_stock_count_by_market.side_effect = Exception("Service error")
            
            # Act
            response = http_client.get("/api/v1/sync/stocks/count")
            
            # Assert
            assert response.status_code == 500, "API should return 500 for service errors"
            error_data = response.json()
            assert "error" in error_data.get("detail", "").lower(), "Should contain error message"

    def test_api_database_session_management(self, http_client):
        """Test that API properly manages database sessions."""
        # This test verifies session cleanup by making multiple requests
        # that should not interfere with each other
        
        responses = []
        for i in range(3):
            response = http_client.get("/api/v1/sync/stocks/count") 
            responses.append(response)
        
        # All requests should succeed (no session leaks)
        for response in responses:
            assert response.status_code in [200, 404], "All requests should handle sessions properly"


# Test utilities and helpers
def pytest_configure(config):
    """Configure pytest for E2E API tests."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end API tests")
    config.addinivalue_line("markers", "requires_docker: marks tests that require Docker services")


def pytest_collection_modifyitems(config, items):
    """Mark all tests in this module as requiring Docker services."""
    for item in items:
        if "test_e2e_api" in str(item.fspath):
            item.add_marker(pytest.mark.requires_docker)
            item.add_marker(pytest.mark.e2e)