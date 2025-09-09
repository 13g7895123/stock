"""Unit tests for StockListService - 股票列表擷取服務單元測試."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from src.services.stock_list_service import StockListService
from src.models.stock import Stock


class TestStockListService:
    """Test StockListService core logic - 測試StockListService核心邏輯."""
    
    @pytest.fixture
    def stock_service(self):
        """Create StockListService instance."""
        return StockListService()
    
    @pytest.fixture
    def mock_tse_api_response(self):
        """Mock TSE API response data."""
        return {
            "data": [
                ["1101", "台泥", "水泥工業"],
                ["1102", "亞泥", "水泥工業"],
                ["2330", "台積電", "半導體業"],
                ["0050", "元大台灣50", "ETF"],  # Should be filtered out
                ["00878", "國泰永續高股息", "ETF"],  # Should be filtered out
                ["12345", "測試股", "測試業"],  # Should be filtered out (5 digits)
            ]
        }
    
    @pytest.fixture
    def mock_tpex_api_response(self):
        """Mock TPEx OpenAPI response data."""
        return [
            {
                "SecuritiesCompanyCode": "3008",
                "CompanyName": "大立光電股份有限公司",
                "CompanyAbbreviation": "大立光"
            },
            {
                "SecuritiesCompanyCode": "4938",
                "CompanyName": "和碩聯合科技股份有限公司",
                "CompanyAbbreviation": "和碩"
            },
            {
                "SecuritiesCompanyCode": "06208",
                "CompanyName": "富邦台50基金",
                "CompanyAbbreviation": "富邦台50"  # Should be filtered out
            }
        ]
    
    @pytest.fixture
    def expected_filtered_stocks(self):
        """Expected filtered stock data."""
        return [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "1102", "name": "亞泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "3008", "name": "大立光電股份有限公司", "market": "TPEx"},
            {"symbol": "4938", "name": "和碩聯合科技股份有限公司", "market": "TPEx"},
        ]
    
    def test_filter_valid_stocks_should_exclude_etfs_and_invalid_symbols(self, stock_service):
        """Test filtering logic excludes ETFs and invalid stock symbols."""
        # Arrange
        raw_stocks = [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "0050", "name": "元大台灣50", "market": "TSE"},  # ETF - should be excluded
            {"symbol": "00878", "name": "國泰永續高股息", "market": "TSE"},  # ETF - should be excluded
            {"symbol": "12345", "name": "測試股", "market": "TSE"},  # 5 digits - should be excluded
            {"symbol": "ABC", "name": "測試", "market": "TSE"},  # Non-numeric - should be excluded
        ]
        
        # Act
        filtered_stocks = stock_service.filter_valid_stocks(raw_stocks)
        
        # Assert
        assert len(filtered_stocks) == 2
        assert filtered_stocks[0]["symbol"] == "1101"
        assert filtered_stocks[1]["symbol"] == "2330"
        
        # Verify no ETFs or invalid symbols are included
        symbols = [stock["symbol"] for stock in filtered_stocks]
        assert "0050" not in symbols
        assert "00878" not in symbols
        assert "12345" not in symbols
        assert "ABC" not in symbols
    
    def test_filter_valid_stocks_should_include_four_digit_non_zero_prefix(self, stock_service):
        """Test filtering includes only 4-digit stocks not starting with 0."""
        # Arrange
        raw_stocks = [
            {"symbol": "1000", "name": "測試1", "market": "TSE"},  # Valid
            {"symbol": "9999", "name": "測試2", "market": "TSE"},  # Valid
            {"symbol": "0001", "name": "測試3", "market": "TSE"},  # Invalid - starts with 0
            {"symbol": "999", "name": "測試4", "market": "TSE"},   # Invalid - 3 digits
            {"symbol": "10000", "name": "測試5", "market": "TSE"}, # Invalid - 5 digits
        ]
        
        # Act
        filtered_stocks = stock_service.filter_valid_stocks(raw_stocks)
        
        # Assert
        assert len(filtered_stocks) == 2
        symbols = [stock["symbol"] for stock in filtered_stocks]
        assert "1000" in symbols
        assert "9999" in symbols
        assert "0001" not in symbols
        assert "999" not in symbols
        assert "10000" not in symbols
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_should_return_formatted_data(self, stock_service, mock_tse_api_response):
        """Test fetching TSE stocks returns properly formatted data."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_tse_api_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tse_stocks()
            
            # Assert
            assert len(stocks) == 6  # All raw data before filtering
            assert stocks[0]["symbol"] == "1101"
            assert stocks[0]["name"] == "台泥"
            assert stocks[0]["market"] == "TSE"
            assert stocks[0]["industry"] == "水泥工業"
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_should_return_formatted_data(self, stock_service, mock_tpex_api_response):
        """Test fetching TPEx stocks returns properly formatted data."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_tpex_api_response
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Act
            stocks = await stock_service.fetch_tpex_stocks()
            
            # Assert
            assert len(stocks) == 3  # All raw data before filtering
            assert stocks[0]["symbol"] == "3008"
            assert stocks[0]["name"] == "大立光電股份有限公司"
            assert stocks[0]["market"] == "TPEx"
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_should_raise_exception_on_api_failure(self, stock_service):
        """Test TSE API failure handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("API connection failed")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await stock_service.fetch_tse_stocks()
            
            assert "API connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_tpex_stocks_should_raise_exception_on_api_failure(self, stock_service):
        """Test TPEx API failure handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("API connection failed")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await stock_service.fetch_tpex_stocks()
            
            assert "API connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_tse_stocks_should_handle_http_error_status(self, stock_service):
        """Test TSE API HTTP error status handling."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Server error"}
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await stock_service.fetch_tse_stocks()
            
            assert "500" in str(exc_info.value) or "HTTP" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_all_stocks_should_combine_tse_and_tpex_data(
        self, stock_service, mock_tse_api_response, mock_tpex_api_response
    ):
        """Test fetching all stocks combines and filters TSE and TPEx data."""
        # Arrange
        with patch.object(stock_service, 'fetch_tse_stocks') as mock_tse, \
             patch.object(stock_service, 'fetch_tpex_stocks') as mock_tpex:
            
            # Mock return data (already formatted)
            mock_tse.return_value = [
                {"symbol": "1101", "name": "台泥", "market": "TSE"},
                {"symbol": "0050", "name": "元大台灣50", "market": "TSE"},
            ]
            mock_tpex.return_value = [
                {"symbol": "3008", "name": "大立光電股份有限公司", "market": "TPEx"},
                {"symbol": "06208", "name": "富邦台50基金", "market": "TPEx"},
            ]
            
            # Act
            all_stocks, errors = await stock_service.fetch_all_stocks()
            
            # Assert
            assert len(all_stocks) == 2  # Only non-ETF stocks
            assert len(errors) == 0  # No errors expected
            symbols = [stock["symbol"] for stock in all_stocks]
            assert "1101" in symbols
            assert "3008" in symbols
            assert "0050" not in symbols  # ETF should be filtered out
            assert "06208" not in symbols  # ETF should be filtered out
    
    def test_validate_stock_data_should_accept_valid_data(self, stock_service):
        """Test stock data validation accepts valid data."""
        # Arrange
        valid_stock = {
            "symbol": "2330",
            "name": "台積電",
            "market": "TSE",
            "industry": "半導體業"
        }
        
        # Act & Assert (should not raise exception)
        stock_service.validate_stock_data(valid_stock)
    
    def test_validate_stock_data_should_reject_missing_required_fields(self, stock_service):
        """Test stock data validation rejects data with missing required fields."""
        # Arrange
        invalid_stocks = [
            {"name": "台積電", "market": "TSE"},  # Missing symbol
            {"symbol": "2330", "market": "TSE"},  # Missing name
            {"symbol": "2330", "name": "台積電"},  # Missing market
        ]
        
        # Act & Assert
        for invalid_stock in invalid_stocks:
            with pytest.raises(ValueError) as exc_info:
                stock_service.validate_stock_data(invalid_stock)
            
            assert "required field" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()
    
    def test_validate_stock_data_should_reject_empty_values(self, stock_service):
        """Test stock data validation rejects empty values."""
        # Arrange
        invalid_stocks = [
            {"symbol": "", "name": "台積電", "market": "TSE"},
            {"symbol": "2330", "name": "", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": ""},
        ]
        
        # Act & Assert
        for invalid_stock in invalid_stocks:
            with pytest.raises(ValueError) as exc_info:
                stock_service.validate_stock_data(invalid_stock)
            
            assert "empty" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()