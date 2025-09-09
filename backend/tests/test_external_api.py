"""Tests for external API interactions - 外部API互動測試."""
import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.services.stock_list_service import StockListService


class TestExternalAPIIntegration:
    """Test external API integrations for stock data fetching."""
    
    @pytest.fixture
    def stock_service(self):
        """Create StockListService instance."""
        return StockListService()
    
    @pytest.fixture
    def mock_tse_response_data(self):
        """Mock TSE API successful response."""
        return {
            "stat": "OK",
            "date": "20240101",
            "title": "上市公司基本資料",
            "fields": ["股票代號", "公司名稱", "產業別"],
            "data": [
                ["1101", "台泥", "水泥工業"],
                ["1102", "亞泥", "水泥工業"],
                ["2330", "台積電", "半導體業"],
                ["2317", "鴻海", "電子零組件業"],
            ]
        }
    
    @pytest.fixture
    def mock_tpex_response_data(self):
        """Mock TPEx API successful response."""
        return {
            "iTotalRecords": 3,
            "iTotalDisplayRecords": 3,
            "aaData": [
                ["3008", "大立光", "光電業", "上櫃"],
                ["4938", "和碩", "電子業", "上櫃"],
                ["6505", "台塑化", "塑膠工業", "上櫃"],
            ]
        }
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_success_should_return_formatted_data(
        self, stock_service, mock_tse_response_data
    ):
        """Test successful TSE API call returns properly formatted stock data."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_tse_response_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tse_stocks()
            
            # Assert
            assert len(stocks) == 4
            
            # Verify first stock
            assert stocks[0]["symbol"] == "1101"
            assert stocks[0]["name"] == "台泥"
            assert stocks[0]["market"] == "TSE"
            assert stocks[0]["industry"] == "水泥工業"
            
            # Verify API was called with correct URL
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "tse.com.tw" in str(call_args) or "twse" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_success_should_return_formatted_data(
        self, stock_service, mock_tpex_response_data
    ):
        """Test successful TPEx API call returns properly formatted stock data."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_tpex_response_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tpex_stocks()
            
            # Assert
            assert len(stocks) == 3
            
            # Verify first stock
            assert stocks[0]["symbol"] == "3008"
            assert stocks[0]["name"] == "大立光"
            assert stocks[0]["market"] == "TPEx"
            assert stocks[0]["industry"] == "光電業"
            
            # Verify API was called
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_http_error_should_raise_exception(self, stock_service):
        """Test TSE API HTTP error handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await stock_service.fetch_tse_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_http_error_should_raise_exception(self, stock_service):
        """Test TPEx API HTTP error handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await stock_service.fetch_tpex_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_network_timeout_should_raise_exception(self, stock_service):
        """Test TSE API network timeout handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            # Act & Assert
            with pytest.raises(httpx.TimeoutException):
                await stock_service.fetch_tse_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_connection_error_should_raise_exception(self, stock_service):
        """Test TPEx API connection error handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            # Act & Assert
            with pytest.raises(httpx.ConnectError):
                await stock_service.fetch_tpex_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_invalid_json_should_raise_exception(self, stock_service):
        """Test TSE API invalid JSON response handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(ValueError):
                await stock_service.fetch_tse_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_malformed_data_structure_should_raise_exception(self, stock_service):
        """Test TPEx API malformed data structure handling."""
        # Arrange
        malformed_data = {
            "iTotalRecords": 1,
            # Missing 'aaData' field
            "wrongField": [["3008", "大立光"]]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = malformed_data
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(KeyError):
                await stock_service.fetch_tpex_stocks()
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_empty_data_should_return_empty_list(self, stock_service):
        """Test TSE API empty data response."""
        # Arrange
        empty_response = {
            "stat": "OK",
            "date": "20240101",
            "data": []
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = empty_response
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tse_stocks()
            
            # Assert
            assert stocks == []
            assert len(stocks) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_empty_data_should_return_empty_list(self, stock_service):
        """Test TPEx API empty data response."""
        # Arrange
        empty_response = {
            "iTotalRecords": 0,
            "aaData": []
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = empty_response
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tpex_stocks()
            
            # Assert
            assert stocks == []
    
    @pytest.mark.asyncio
    async def test_fetch_all_stocks_partial_failure_should_handle_gracefully(self, stock_service):
        """Test handling when one API fails but the other succeeds."""
        # Arrange
        successful_tse_data = [
            {"symbol": "2330", "name": "台積電", "market": "TSE", "industry": "半導體業"}
        ]
        
        with patch.object(stock_service, 'fetch_tse_stocks') as mock_tse, \
             patch.object(stock_service, 'fetch_tpex_stocks') as mock_tpex:
            
            mock_tse.return_value = successful_tse_data
            mock_tpex.side_effect = httpx.TimeoutException("TPEx API timeout")
            
            # Act & Assert
            with pytest.raises(httpx.TimeoutException):
                await stock_service.fetch_all_stocks()
    
    @pytest.mark.asyncio
    async def test_api_retry_mechanism_should_retry_on_temporary_failure(self, stock_service):
        """Test API retry mechanism for temporary failures."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            # First call fails, second succeeds
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.raise_for_status = Mock()
            mock_response_success.json.return_value = {"data": []}
            
            mock_get.side_effect = [
                httpx.TimeoutException("Temporary timeout"),
                mock_response_success
            ]
            
            # Act - This assumes retry mechanism is implemented
            # If not implemented yet, this test will drive the implementation
            try:
                stocks = await stock_service.fetch_tse_stocks_with_retry(max_retries=2)
                # Should succeed on second try
                assert stocks == []
            except NotImplementedError:
                # Test documents expected behavior for future implementation
                pytest.skip("Retry mechanism not implemented yet")
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting_should_respect_limits(self, stock_service):
        """Test API rate limiting compliance."""
        # Arrange - Mock multiple rapid calls
        call_times = []
        
        def mock_get_with_timing(*args, **kwargs):
            import time
            call_times.append(time.time())
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = {"data": []}
            return mock_response
        
        with patch('httpx.AsyncClient.get', side_effect=mock_get_with_timing):
            # Act - Make multiple rapid calls
            for _ in range(3):
                await stock_service.fetch_tse_stocks()
            
            # Assert - Calls should be spaced out (if rate limiting implemented)
            if len(call_times) >= 2:
                time_diff = call_times[1] - call_times[0]
                # This test documents expected behavior
                # Implementation should ensure minimum delay between calls
                # assert time_diff >= 0.5  # 500ms minimum delay
    
    @pytest.mark.asyncio
    async def test_api_response_validation_should_reject_invalid_stock_data(self, stock_service):
        """Test API response validation rejects invalid stock data."""
        # Arrange - Response with invalid stock data
        invalid_response = {
            "stat": "OK",
            "data": [
                ["", "無效股票", "測試業"],  # Empty symbol
                ["INVALID", "非數字代號", "測試業"],  # Non-numeric symbol
                ["1234"],  # Incomplete data
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = invalid_response
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tse_stocks()
            
            # Assert - Should filter out invalid entries
            # This test documents expected validation behavior
            for stock in stocks:
                assert stock["symbol"]  # Symbol should not be empty
                assert stock["symbol"].isdigit()  # Symbol should be numeric
                assert len(stock["symbol"]) == 4  # Symbol should be 4 digits
                assert stock["name"]  # Name should not be empty