"""Integration Test Configuration and Fixtures.

This module provides additional fixtures specifically for integration tests
that require real database connections and external services.
"""
import pytest
import asyncio
import time
from typing import Generator, Dict, Any
import httpx
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import settings
from src.models.stock import Stock


# Integration test database URLs
POSTGRES_TEST_URL = "postgresql://stock_user:password@localhost:5432/stock_analysis"
API_BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def postgres_engine():
    """Create PostgreSQL engine for integration tests."""
    engine = create_engine(POSTGRES_TEST_URL, echo=False, pool_pre_ping=True)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def postgres_session_factory(postgres_engine):
    """Create session factory for PostgreSQL integration tests."""
    return sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)


@pytest.fixture
def postgres_session(postgres_session_factory) -> Generator[Session, None, None]:
    """Create PostgreSQL session for integration tests."""
    session = postgres_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
async def async_postgres_pool():
    """Create async PostgreSQL connection pool for async tests."""
    try:
        pool = await asyncpg.create_pool(
            "postgresql://stock_user:password@localhost:5432/stock_analysis",
            min_size=1,
            max_size=5
        )
        yield pool
    except Exception as e:
        pytest.skip(f"Async PostgreSQL not available: {e}")
    finally:
        if 'pool' in locals():
            await pool.close()


@pytest.fixture
def wait_for_api():
    """Wait for API to be ready before running tests."""
    def _wait_for_api(timeout: int = 30) -> bool:
        """Wait for API to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{API_BASE_URL}/health")
                    if response.status_code == 200:
                        return True
            except Exception:
                pass
            time.sleep(2)
        return False
    
    return _wait_for_api


@pytest.fixture
def api_client(wait_for_api):
    """Create HTTP client for API integration tests."""
    # Ensure API is ready
    if not wait_for_api(30):
        pytest.skip("API not available within timeout")
    
    client = httpx.Client(
        base_url=API_BASE_URL,
        timeout=30.0,
        follow_redirects=True
    )
    
    yield client
    client.close()


@pytest.fixture
async def async_api_client(wait_for_api):
    """Create async HTTP client for API integration tests."""
    # Ensure API is ready
    if not wait_for_api(30):
        pytest.skip("API not available within timeout")
    
    async with httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=30.0,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture
def clean_test_stocks(postgres_session):
    """Clean test stocks before and after test."""
    def cleanup():
        """Remove test stocks from database."""
        try:
            # Remove stocks with test symbols
            test_patterns = ['9%', '8%', '7%']  # Test symbol patterns
            for pattern in test_patterns:
                postgres_session.execute(
                    text("DELETE FROM stocks WHERE symbol LIKE :pattern"),
                    {"pattern": pattern}
                )
            
            # Remove specific test symbols
            test_symbols = ['1101', '2330', '3008', '4938', '6505']
            for symbol in test_symbols:
                postgres_session.execute(
                    text("DELETE FROM stocks WHERE symbol = :symbol"),
                    {"symbol": symbol}
                )
            
            postgres_session.commit()
        except Exception:
            postgres_session.rollback()
    
    # Clean before test
    cleanup()
    yield
    # Clean after test
    cleanup()


@pytest.fixture
def sample_taiwan_stocks():
    """Sample Taiwan stock data for testing."""
    return [
        {"symbol": "1101", "name": "台泥", "market": "TSE"},
        {"symbol": "1102", "name": "亞泥", "market": "TSE"}, 
        {"symbol": "2330", "name": "台積電", "market": "TSE"},
        {"symbol": "2317", "name": "鴻海", "market": "TSE"},
        {"symbol": "3008", "name": "大立光", "market": "TPEx"},
        {"symbol": "4938", "name": "和碩", "market": "TPEx"},
        {"symbol": "6505", "name": "台塑化", "market": "TPEx"},
    ]


@pytest.fixture
def insert_test_stocks(postgres_session):
    """Helper fixture to insert test stocks into database."""
    def _insert_stocks(stocks_data: list) -> list:
        """Insert stocks and return created stock objects."""
        created_stocks = []
        for stock_data in stocks_data:
            stock = Stock(
                symbol=stock_data["symbol"],
                name=stock_data["name"],
                market=stock_data["market"],
                industry=stock_data.get("industry"),
                is_active=stock_data.get("is_active", True)
            )
            postgres_session.add(stock)
            created_stocks.append(stock)
        
        postgres_session.commit()
        return created_stocks
    
    return _insert_stocks


@pytest.fixture
def mock_external_apis():
    """Mock external stock APIs for consistent testing."""
    def _create_mocks(tse_data=None, tpex_data=None):
        """Create mock responses for external APIs."""
        if tse_data is None:
            tse_data = [
                ["1101", "台泥"],
                ["2330", "台積電"],
            ]
        
        if tpex_data is None:
            tpex_data = [
                ["3008", "大立光"],
                ["4938", "和碩"],
            ]
        
        return {
            "tse_response": {
                "stat": "OK",
                "data": tse_data
            },
            "tpex_response": {
                "stat": "OK", 
                "aaData": tpex_data
            }
        }
    
    return _create_mocks


@pytest.fixture(scope="session")
def docker_services_ready():
    """Verify that all Docker services are ready."""
    services = {
        "api": {"url": f"{API_BASE_URL}/health", "timeout": 30},
        "postgres": {"check": "postgresql connection", "timeout": 20}
    }
    
    # Check API
    api_ready = False
    start_time = time.time()
    while time.time() - start_time < services["api"]["timeout"]:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(services["api"]["url"])
                if response.status_code == 200:
                    api_ready = True
                    break
        except Exception:
            pass
        time.sleep(2)
    
    if not api_ready:
        pytest.skip("API service not ready")
    
    # Check PostgreSQL
    postgres_ready = False
    try:
        engine = create_engine(POSTGRES_TEST_URL, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        postgres_ready = True
        engine.dispose()
    except Exception:
        pass
    
    if not postgres_ready:
        pytest.skip("PostgreSQL service not ready")
    
    return {"api": api_ready, "postgres": postgres_ready}


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property 
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
        
        def assert_within(self, max_seconds: float, message: str = ""):
            elapsed = self.elapsed
            if elapsed is None:
                raise ValueError("Timer not properly started/stopped")
            assert elapsed <= max_seconds, f"{message} Expected <= {max_seconds}s, got {elapsed:.3f}s"
    
    return PerformanceTimer()


@pytest.fixture
def database_state_checker(postgres_session):
    """Helper to check database state during tests."""
    class DatabaseStateChecker:
        def __init__(self, session: Session):
            self.session = session
        
        def count_stocks(self, active_only: bool = True, market: str = None) -> int:
            query = self.session.query(Stock)
            if active_only:
                query = query.filter(Stock.is_active == True)
            if market:
                query = query.filter(Stock.market == market)
            return query.count()
        
        def get_stock(self, symbol: str) -> Stock:
            return self.session.query(Stock).filter(Stock.symbol == symbol).first()
        
        def verify_stock_exists(self, symbol: str, expected_name: str = None) -> bool:
            stock = self.get_stock(symbol)
            if stock is None:
                return False
            if expected_name and stock.name != expected_name:
                return False
            return True
        
        def get_market_counts(self) -> Dict[str, int]:
            from sqlalchemy import func
            counts = self.session.query(
                Stock.market,
                func.count(Stock.id)
            ).filter(Stock.is_active == True).group_by(Stock.market).all()
            return {market: count for market, count in counts}
    
    return DatabaseStateChecker(postgres_session)


# Pytest configuration for integration tests
def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "postgres: marks tests that require PostgreSQL")
    config.addinivalue_line("markers", "api: marks tests that require API service")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "docker: marks tests that require Docker services")


def pytest_runtest_setup(item):
    """Setup for each integration test."""
    # Skip integration tests if running in CI without services
    import os
    if os.environ.get("SKIP_INTEGRATION_TESTS"):
        if any(mark in item.keywords for mark in ["integration", "postgres", "api", "docker"]):
            pytest.skip("Integration tests skipped in this environment")


# Test data generators
@pytest.fixture
def generate_test_stocks():
    """Generate test stock data."""
    def _generate(count: int = 10, symbol_prefix: str = "9") -> list:
        """Generate test stock data."""
        stocks = []
        for i in range(count):
            symbol = f"{symbol_prefix}{str(i).zfill(3)}"
            stocks.append({
                "symbol": symbol,
                "name": f"測試股票{symbol}",
                "market": "TSE" if i % 2 == 0 else "TPEx",
                "industry": f"測試產業{i % 5}"
            })
        return stocks
    
    return _generate