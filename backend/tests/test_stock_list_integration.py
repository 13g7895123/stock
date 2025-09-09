"""Integration tests for StockListService with database - 股票列表服務資料庫整合測試."""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch, Mock

from src.services.stock_list_service import StockListService
from src.models.stock import Stock


class TestStockListServiceIntegration:
    """Test StockListService database integration - 測試StockListService資料庫整合."""
    
    @pytest.fixture
    def stock_service(self, db_session):
        """Create StockListService with database session."""
        return StockListService(db_session)
    
    @pytest.fixture
    def sample_stock_data(self):
        """Sample stock data for testing."""
        return [
            {"symbol": "1101", "name": "台泥", "market": "TSE", "industry": "水泥工業"},
            {"symbol": "2330", "name": "台積電", "market": "TSE", "industry": "半導體業"},
            {"symbol": "3008", "name": "大立光", "market": "TPEx", "industry": "光電業"},
        ]
    
    @pytest.fixture
    def existing_stocks(self, db_session):
        """Create existing stocks in database for update testing."""
        stocks = [
            Stock(symbol="1101", name="台灣水泥", market="TSE", industry="水泥工業"),  # Name will be updated
            Stock(symbol="2330", name="台積電", market="TSE", industry="半導體業"),    # No change
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()
        
        return stocks
    
    def test_save_stocks_to_database_should_create_new_stocks(self, stock_service, db_session, sample_stock_data):
        """Test saving new stocks to database creates new records."""
        # Arrange - Database should be empty initially
        assert db_session.query(Stock).count() == 0
        
        # Act
        stock_service.save_stocks_to_database(sample_stock_data)
        
        # Assert
        saved_stocks = db_session.query(Stock).all()
        assert len(saved_stocks) == 3
        
        # Verify data integrity
        stock_by_symbol = {stock.symbol: stock for stock in saved_stocks}
        
        assert stock_by_symbol["1101"].name == "台泥"
        assert stock_by_symbol["1101"].market == "TSE"
        assert stock_by_symbol["1101"].industry == "水泥工業"
        assert stock_by_symbol["1101"].is_active is True
        
        assert stock_by_symbol["2330"].name == "台積電"
        assert stock_by_symbol["3008"].market == "TPEx"
    
    def test_save_stocks_to_database_should_update_existing_stocks(
        self, stock_service, db_session, existing_stocks
    ):
        """Test saving stocks updates existing records and creates new ones."""
        # Arrange
        update_data = [
            {"symbol": "1101", "name": "台泥", "market": "TSE", "industry": "水泥工業"},  # Update name
            {"symbol": "2330", "name": "台積電", "market": "TSE", "industry": "半導體業"},    # No change
            {"symbol": "3008", "name": "大立光", "market": "TPEx", "industry": "光電業"},   # New stock
        ]
        
        # Verify initial state
        assert db_session.query(Stock).count() == 2
        
        # Act
        stock_service.save_stocks_to_database(update_data)
        
        # Assert
        all_stocks = db_session.query(Stock).all()
        assert len(all_stocks) == 3
        
        # Verify updates
        updated_stock = db_session.query(Stock).filter_by(symbol="1101").first()
        assert updated_stock.name == "台泥"  # Should be updated
        
        # Verify no change
        unchanged_stock = db_session.query(Stock).filter_by(symbol="2330").first()
        assert unchanged_stock.name == "台積電"
        
        # Verify new stock
        new_stock = db_session.query(Stock).filter_by(symbol="3008").first()
        assert new_stock is not None
        assert new_stock.name == "大立光"
        assert new_stock.market == "TPEx"
    
    def test_save_stocks_to_database_should_handle_duplicate_symbols(
        self, stock_service, db_session, sample_stock_data
    ):
        """Test handling of duplicate symbols in input data."""
        # Arrange - Add duplicate with different name
        duplicate_data = sample_stock_data + [
            {"symbol": "1101", "name": "台灣水泥公司", "market": "TSE", "industry": "水泥工業"}
        ]
        
        # Act
        stock_service.save_stocks_to_database(duplicate_data)
        
        # Assert - Should only have one record per symbol, last one wins
        stocks_1101 = db_session.query(Stock).filter_by(symbol="1101").all()
        assert len(stocks_1101) == 1
        
        # The name should be from the last occurrence in the data
        assert stocks_1101[0].name == "台灣水泥公司"
        
        # Total count should be 3 (not 4)
        assert db_session.query(Stock).count() == 3
    
    def test_get_stocks_from_database_should_return_all_active_stocks(
        self, stock_service, db_session, existing_stocks
    ):
        """Test retrieving all active stocks from database."""
        # Arrange - Add an inactive stock
        inactive_stock = Stock(symbol="9999", name="測試股票", market="TSE", is_active=False)
        db_session.add(inactive_stock)
        db_session.commit()
        
        # Act
        active_stocks = stock_service.get_stocks_from_database()
        
        # Assert
        assert len(active_stocks) == 2  # Only active stocks
        symbols = [stock.symbol for stock in active_stocks]
        assert "1101" in symbols
        assert "2330" in symbols
        assert "9999" not in symbols  # Inactive stock should be excluded
    
    def test_get_stocks_from_database_should_return_empty_list_when_no_stocks(
        self, stock_service, db_session
    ):
        """Test retrieving stocks from empty database returns empty list."""
        # Act
        stocks = stock_service.get_stocks_from_database()
        
        # Assert
        assert stocks == []
        assert len(stocks) == 0
    
    def test_deactivate_missing_stocks_should_mark_old_stocks_inactive(
        self, stock_service, db_session, existing_stocks
    ):
        """Test deactivating stocks that are no longer in the fetched data."""
        # Arrange - New data doesn't include 1101
        current_symbols = ["2330", "3008"]  # Missing 1101
        
        # Act
        stock_service.deactivate_missing_stocks(current_symbols)
        
        # Assert
        stock_1101 = db_session.query(Stock).filter_by(symbol="1101").first()
        stock_2330 = db_session.query(Stock).filter_by(symbol="2330").first()
        
        assert stock_1101.is_active is False  # Should be deactivated
        assert stock_2330.is_active is True   # Should remain active
    
    def test_get_stock_count_by_market_should_return_correct_counts(
        self, stock_service, db_session, sample_stock_data
    ):
        """Test getting stock counts grouped by market."""
        # Arrange
        stock_service.save_stocks_to_database(sample_stock_data)
        
        # Act
        counts = stock_service.get_stock_count_by_market()
        
        # Assert
        assert counts["TSE"] == 2  # 1101, 2330
        assert counts["TPEx"] == 1  # 3008
        assert sum(counts.values()) == 3
    
    @pytest.mark.asyncio
    async def test_sync_all_stocks_should_perform_complete_sync_process(
        self, stock_service, db_session, existing_stocks
    ):
        """Test complete stock synchronization process."""
        # Arrange - Mock external API calls
        mock_api_data = [
            {"symbol": "1101", "name": "台泥", "market": "TSE", "industry": "水泥工業"},
            {"symbol": "2330", "name": "台積電", "market": "TSE", "industry": "半導體業"},
            {"symbol": "3008", "name": "大立光", "market": "TPEx", "industry": "光電業"},
            {"symbol": "4938", "name": "和碩", "market": "TPEx", "industry": "電子業"},
        ]
        
        with patch.object(stock_service, 'fetch_all_stocks') as mock_fetch:
            mock_fetch.return_value = mock_api_data
            
            # Act
            result = await stock_service.sync_all_stocks()
            
            # Assert
            assert result["success"] is True
            assert result["total_stocks"] == 4
            assert result["new_stocks"] == 2      # 3008, 4938 are new
            assert result["updated_stocks"] == 2  # 1101, 2330 already existed
            
            # Verify database state
            all_stocks = db_session.query(Stock).filter_by(is_active=True).all()
            assert len(all_stocks) == 4
            
            symbols = [stock.symbol for stock in all_stocks]
            assert set(symbols) == {"1101", "2330", "3008", "4938"}
    
    def test_save_stocks_to_database_should_handle_database_error_gracefully(
        self, stock_service, db_session, sample_stock_data
    ):
        """Test handling database errors during stock saving."""
        # Arrange - Mock database session to raise an error
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database connection failed")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                stock_service.save_stocks_to_database(sample_stock_data)
            
            assert "Database connection failed" in str(exc_info.value)
            
            # Verify rollback was called
            # In real implementation, should verify transaction rollback
    
    def test_save_stocks_with_invalid_data_should_raise_validation_error(
        self, stock_service, db_session
    ):
        """Test saving invalid stock data raises validation error."""
        # Arrange
        invalid_data = [
            {"symbol": "", "name": "Invalid Stock", "market": "TSE"},  # Empty symbol
        ]
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            stock_service.save_stocks_to_database(invalid_data)
        
        assert "validation" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
        
        # Verify no data was saved
        assert db_session.query(Stock).count() == 0
    
    def test_bulk_operations_performance_with_large_dataset(self, stock_service, db_session):
        """Test performance with large dataset (simulate real-world scenario)."""
        # Arrange - Create large dataset (simulate ~2000 stocks)
        large_dataset = []
        for i in range(1000, 3000):  # 2000 stocks
            large_dataset.append({
                "symbol": str(i),
                "name": f"測試股票{i}",
                "market": "TSE" if i % 2 == 0 else "TPEx",
                "industry": f"產業{i % 10}"
            })
        
        # Act & Assert - Should complete without timeout
        import time
        start_time = time.time()
        
        stock_service.save_stocks_to_database(large_dataset)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert execution_time < 30  # 30 seconds threshold
        assert db_session.query(Stock).count() == 2000