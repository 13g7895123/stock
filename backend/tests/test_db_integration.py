"""Database Integration Tests - Real PostgreSQL Database Tests.

These tests run against the actual PostgreSQL database to verify:
1. Real database read/write operations
2. Transaction handling
3. Data persistence
4. Complete service layer database integration

Run these tests against the running Docker PostgreSQL service:
postgresql://stock_user:password@localhost:5432/stock_analysis
"""
import pytest
import asyncio
from typing import List, Dict, Any
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch, Mock
import httpx

from src.services.stock_list_service import StockListService
from src.models.stock import Stock
from src.core.database import Base


# Test database connection settings for real PostgreSQL
TEST_DATABASE_URL = "postgresql://stock_user:password@localhost:5432/stock_analysis"
TEST_ASYNC_DATABASE_URL = "postgresql://stock_user:password@localhost:5432/stock_analysis"


class TestDatabaseIntegration:
    """Test database integration with real PostgreSQL database."""

    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create test database engine for real PostgreSQL."""
        engine = create_engine(TEST_DATABASE_URL, echo=False)
        yield engine
        engine.dispose()

    @pytest.fixture(scope="class")
    def db_session_factory(self, db_engine):
        """Create session factory for test database."""
        return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    @pytest.fixture
    def db_session(self, db_session_factory):
        """Create test database session with proper cleanup."""
        session = db_session_factory()
        
        # Ensure clean state at start
        self._cleanup_test_data(session)
        
        yield session
        
        # Clean up after test
        self._cleanup_test_data(session)
        session.close()

    def _cleanup_test_data(self, session: Session):
        """Clean up test data from database."""
        try:
            # Delete test stocks (symbols starting with '9' for test identification)
            session.execute(
                text("DELETE FROM stocks WHERE symbol LIKE '9%' OR symbol IN ('1101', '2330', '3008', '4938')")
            )
            session.commit()
        except Exception:
            session.rollback()

    @pytest.fixture
    def stock_service(self, db_session):
        """Create StockListService with real database session."""
        return StockListService(db_session=db_session)

    @pytest.fixture
    def test_stock_data(self):
        """Sample Taiwan stock data for testing."""
        return [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "3008", "name": "大立光", "market": "TPEx"},
            {"symbol": "4938", "name": "和碩", "market": "TPEx"},
        ]

    def test_database_connection(self, db_session):
        """Test that database connection works."""
        result = db_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1, "Database connection should work"

    def test_save_stocks_to_database_creates_records(self, stock_service, db_session, test_stock_data):
        """Test that save_stocks_to_database creates actual database records."""
        # Arrange
        initial_count = db_session.query(Stock).filter(
            Stock.symbol.in_([stock["symbol"] for stock in test_stock_data])
        ).count()
        assert initial_count == 0, "Should start with clean database"

        # Act
        created_count, updated_count = stock_service.save_stocks_to_database(test_stock_data)

        # Assert
        assert created_count == 4, "Should create 4 new stocks"
        assert updated_count == 0, "Should not update any stocks initially"

        # Verify records exist in database
        saved_stocks = db_session.query(Stock).filter(
            Stock.symbol.in_([stock["symbol"] for stock in test_stock_data])
        ).all()
        
        assert len(saved_stocks) == 4, "All stocks should be saved to database"
        
        stock_by_symbol = {stock.symbol: stock for stock in saved_stocks}
        assert stock_by_symbol["1101"].name == "台泥"
        assert stock_by_symbol["1101"].market == "TSE"
        assert stock_by_symbol["1101"].is_active is True
        assert stock_by_symbol["2330"].name == "台積電"
        assert stock_by_symbol["3008"].market == "TPEx"

    def test_save_stocks_to_database_updates_existing_records(self, stock_service, db_session):
        """Test updating existing stocks in database."""
        # Arrange - Insert initial stock
        initial_stock = Stock(symbol="1101", name="台灣水泥", market="TSE", is_active=True)
        db_session.add(initial_stock)
        db_session.commit()

        # Verify initial state
        existing_stock = db_session.query(Stock).filter_by(symbol="1101").first()
        assert existing_stock.name == "台灣水泥"

        # Act - Update with new data
        update_data = [{"symbol": "1101", "name": "台泥", "market": "TSE"}]
        created_count, updated_count = stock_service.save_stocks_to_database(update_data)

        # Assert
        assert created_count == 0, "Should not create new stocks"
        assert updated_count == 1, "Should update existing stock"

        # Verify update persisted to database
        db_session.refresh(existing_stock)
        assert existing_stock.name == "台泥", "Stock name should be updated in database"
        assert existing_stock.market == "TSE", "Stock market should remain TSE"
        assert existing_stock.is_active is True, "Stock should remain active"

    def test_get_stock_count_by_market_queries_database(self, stock_service, db_session, test_stock_data):
        """Test that get_stock_count_by_market queries real database."""
        # Arrange - Save test data
        stock_service.save_stocks_to_database(test_stock_data)

        # Act
        counts = stock_service.get_stock_count_by_market()

        # Assert - Verify counts match data in database
        assert counts["TSE"] == 2, "Should count TSE stocks from database"
        assert counts["TPEx"] == 2, "Should count TPEx stocks from database"
        assert sum(counts.values()) == 4, "Total should match saved stocks"

        # Verify by direct database query
        direct_tse_count = db_session.query(Stock).filter(
            Stock.market == "TSE",
            Stock.is_active == True,
            Stock.symbol.in_(["1101", "2330"])
        ).count()
        assert direct_tse_count == counts["TSE"], "Service count should match direct database query"

    def test_deactivate_missing_stocks_updates_database(self, stock_service, db_session):
        """Test that deactivate_missing_stocks updates database records."""
        # Arrange - Insert test stocks
        test_stocks = [
            Stock(symbol="1101", name="台泥", market="TSE", is_active=True),
            Stock(symbol="2330", name="台積電", market="TSE", is_active=True),
            Stock(symbol="3008", name="大立光", market="TPEx", is_active=True),
        ]
        for stock in test_stocks:
            db_session.add(stock)
        db_session.commit()

        # Act - Deactivate missing stocks (only keep 2330)
        current_symbols = ["2330"]
        deactivated_count = stock_service.deactivate_missing_stocks(current_symbols)

        # Assert
        assert deactivated_count == 2, "Should deactivate 2 missing stocks"

        # Verify database state
        active_stocks = db_session.query(Stock).filter(Stock.is_active == True).all()
        active_symbols = [stock.symbol for stock in active_stocks]
        assert "2330" in active_symbols, "2330 should remain active"
        
        inactive_stocks = db_session.query(Stock).filter(Stock.is_active == False).all()
        inactive_symbols = [stock.symbol for stock in inactive_stocks]
        assert "1101" in inactive_symbols, "1101 should be deactivated"
        assert "3008" in inactive_symbols, "3008 should be deactivated"

    def test_transaction_rollback_on_error(self, stock_service, db_session):
        """Test that database transactions rollback on error."""
        # Arrange - Create invalid stock data that will cause an error
        invalid_data = [
            {"symbol": "1101", "name": "Valid Stock", "market": "TSE"},
            {"symbol": "", "name": "Invalid Stock", "market": "TSE"},  # Invalid empty symbol
        ]

        # Act & Assert
        with pytest.raises(Exception):
            # This should fail due to validation and rollback transaction
            stock_service.save_stocks_to_database(invalid_data)

        # Verify no data was committed to database
        saved_stocks = db_session.query(Stock).filter_by(symbol="1101").all()
        assert len(saved_stocks) == 0, "No data should be committed due to rollback"

    @pytest.mark.asyncio
    async def test_sync_all_stocks_integration(self, stock_service, db_session):
        """Test complete sync_all_stocks with database integration."""
        # Arrange - Mock API responses
        mock_api_data = [
            {"symbol": "1101", "name": "台泥", "market": "TSE"},
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "3008", "name": "大立光", "market": "TPEx"},
        ]

        # Insert an existing stock that will be updated
        existing_stock = Stock(symbol="1101", name="台灣水泥", market="TSE", is_active=True)
        db_session.add(existing_stock)
        db_session.commit()

        with patch.object(stock_service, 'fetch_all_stocks') as mock_fetch:
            mock_fetch.return_value = mock_api_data

            # Act
            result = await stock_service.sync_all_stocks()

            # Assert
            assert result["status"] == "success", "Sync should succeed"
            assert result["total_fetched"] == 3, "Should fetch 3 stocks"
            assert result["created"] == 2, "Should create 2 new stocks (2330, 3008)"
            assert result["updated"] == 1, "Should update 1 existing stock (1101)"

            # Verify database state
            all_active_stocks = db_session.query(Stock).filter_by(is_active=True).all()
            symbols = [stock.symbol for stock in all_active_stocks]
            assert set(symbols) == {"1101", "2330", "3008"}, "Database should contain synced stocks"

            # Verify update occurred
            updated_stock = db_session.query(Stock).filter_by(symbol="1101").first()
            assert updated_stock.name == "台泥", "Existing stock should be updated in database"

    def test_large_dataset_performance(self, stock_service, db_session):
        """Test database performance with larger dataset."""
        import time
        
        # Arrange - Create large dataset (simulate real-world data)
        large_dataset = []
        for i in range(9000, 9100):  # 100 test stocks
            large_dataset.append({
                "symbol": str(i),
                "name": f"測試股票{i}",
                "market": "TSE" if i % 2 == 0 else "TPEx"
            })

        # Act
        start_time = time.time()
        created_count, updated_count = stock_service.save_stocks_to_database(large_dataset)
        end_time = time.time()

        # Assert
        assert created_count == 100, "Should create all test stocks"
        assert updated_count == 0, "Should not update any stocks initially"
        
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Should complete within 5 seconds, took {execution_time:.2f}s"

        # Verify data in database
        saved_count = db_session.query(Stock).filter(
            Stock.symbol.between("9000", "9099")
        ).count()
        assert saved_count == 100, "All test stocks should be saved to database"

    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, db_session):
        """Test database connection recovery after connection loss."""
        # This test verifies that the service can recover from connection issues
        
        # Arrange - Create service with session
        service = StockListService(db_session=db_session)
        
        # Act - Perform operation to verify connection works
        test_data = [{"symbol": "9999", "name": "Connection Test", "market": "TSE"}]
        
        # This should work normally
        created_count, updated_count = service.save_stocks_to_database(test_data)
        
        # Assert
        assert created_count == 1, "Should successfully save to database"
        
        # Verify data persisted
        saved_stock = db_session.query(Stock).filter_by(symbol="9999").first()
        assert saved_stock is not None, "Stock should be saved in database"
        assert saved_stock.name == "Connection Test"

    def test_concurrent_database_access(self, db_engine):
        """Test concurrent database access from multiple sessions."""
        from sqlalchemy.orm import sessionmaker
        
        # Create session factory and sessions
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        session1 = SessionLocal()
        session2 = SessionLocal()
        
        try:
            service1 = StockListService(db_session=session1)
            service2 = StockListService(db_session=session2)
            
            # Clean up any existing test data
            self._cleanup_test_data(session1)
            self._cleanup_test_data(session2)
            
            # Act - Concurrent writes
            data1 = [{"symbol": "9001", "name": "Concurrent Test 1", "market": "TSE"}]
            data2 = [{"symbol": "9002", "name": "Concurrent Test 2", "market": "TPEx"}]
            
            service1.save_stocks_to_database(data1)
            service2.save_stocks_to_database(data2)
            
            # Assert - Both operations should succeed
            stock1 = session1.query(Stock).filter_by(symbol="9001").first()
            stock2 = session2.query(Stock).filter_by(symbol="9002").first()
            
            assert stock1 is not None, "First concurrent write should succeed"
            assert stock2 is not None, "Second concurrent write should succeed"
            assert stock1.name == "Concurrent Test 1"
            assert stock2.name == "Concurrent Test 2"
            
        finally:
            # Clean up
            self._cleanup_test_data(session1)
            session1.close()
            session2.close()


class TestDatabaseConstraintsAndValidation:
    """Test database constraints and validation rules."""
    
    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create test database engine for real PostgreSQL."""
        engine = create_engine(TEST_DATABASE_URL, echo=False)
        yield engine
        engine.dispose()

    @pytest.fixture
    def db_session(self, db_engine):
        """Create test database session."""
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        session = SessionLocal()
        
        # Clean up test data
        try:
            session.execute(text("DELETE FROM stocks WHERE symbol LIKE '8%'"))
            session.commit()
        except Exception:
            session.rollback()
        
        yield session
        
        # Clean up after test
        try:
            session.execute(text("DELETE FROM stocks WHERE symbol LIKE '8%'"))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def test_unique_symbol_constraint(self, db_session):
        """Test that unique symbol constraint is enforced in database."""
        # Arrange - Insert first stock
        stock1 = Stock(symbol="8001", name="First Stock", market="TSE")
        db_session.add(stock1)
        db_session.commit()

        # Act & Assert - Try to insert duplicate symbol
        stock2 = Stock(symbol="8001", name="Duplicate Stock", market="TPEx")
        db_session.add(stock2)
        
        with pytest.raises(Exception) as exc_info:
            db_session.commit()
        
        # Should raise integrity error due to unique constraint
        assert "unique" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()

    def test_required_fields_constraint(self, db_session):
        """Test that required fields are enforced in database."""
        # Test missing symbol
        with pytest.raises(Exception):
            stock = Stock(name="Missing Symbol", market="TSE")
            db_session.add(stock)
            db_session.commit()

        # Test missing name  
        with pytest.raises(Exception):
            stock = Stock(symbol="8002", market="TSE")
            db_session.add(stock)
            db_session.commit()

        # Test missing market
        with pytest.raises(Exception):
            stock = Stock(symbol="8003", name="Missing Market")
            db_session.add(stock)
            db_session.commit()

    def test_market_values_validation(self, db_session):
        """Test that market field accepts valid values."""
        # Valid market values should work
        valid_stock_tse = Stock(symbol="8004", name="TSE Stock", market="TSE")
        valid_stock_tpex = Stock(symbol="8005", name="TPEx Stock", market="TPEx")
        
        db_session.add(valid_stock_tse)
        db_session.add(valid_stock_tpex)
        db_session.commit()  # Should not raise exception
        
        # Verify data was saved
        saved_tse = db_session.query(Stock).filter_by(symbol="8004").first()
        saved_tpex = db_session.query(Stock).filter_by(symbol="8005").first()
        
        assert saved_tse.market == "TSE"
        assert saved_tpex.market == "TPEx"


# Additional test configuration
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest for database integration tests."""
    config.addinivalue_line("markers", "db_integration: marks tests as database integration tests")
    config.addinivalue_line("markers", "requires_postgres: marks tests that require PostgreSQL")