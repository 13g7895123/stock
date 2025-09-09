"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from src.main import app
from src.core.database import get_db, Base
from src.core.config import settings

# Test database URL (use in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator:
    """Create a test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_stock_data():
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics"
    }


@pytest.fixture
def test_price_data():
    """Sample price data for testing."""
    return {
        "symbol": "AAPL",
        "open_price": 150.0,
        "high_price": 155.0,
        "low_price": 148.0,
        "close_price": 152.0,
        "volume": 1000000
    }


@pytest.fixture
def taiwan_stock_data():
    """Sample Taiwan stock data for testing."""
    return [
        {"symbol": "1101", "name": "台泥", "market": "TSE", "industry": "水泥工業"},
        {"symbol": "2330", "name": "台積電", "market": "TSE", "industry": "半導體業"},
        {"symbol": "3008", "name": "大立光", "market": "TPEx", "industry": "光電業"},
        {"symbol": "4938", "name": "和碩", "market": "TPEx", "industry": "電子業"},
    ]


@pytest.fixture
def mock_tse_api_data():
    """Mock TSE API response data for testing."""
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
            ["0050", "元大台灣50", "ETF"],  # Should be filtered out
        ]
    }


@pytest.fixture
def mock_tpex_api_data():
    """Mock TPEx API response data for testing."""
    return {
        "iTotalRecords": 4,
        "iTotalDisplayRecords": 4,
        "aaData": [
            ["3008", "大立光", "光電業", "上櫃"],
            ["4938", "和碩", "電子業", "上櫃"],
            ["6505", "台塑化", "塑膠工業", "上櫃"],
            ["00878", "國泰永續高股息", "ETF", "上櫃"],  # Should be filtered out
        ]
    }


@pytest.fixture
def invalid_stock_data():
    """Invalid stock data for testing validation."""
    return [
        {"symbol": "", "name": "Empty Symbol", "market": "TSE"},  # Empty symbol
        {"symbol": "0050", "name": "ETF Stock", "market": "TSE"},  # ETF (starts with 0)
        {"symbol": "ABCD", "name": "Non-numeric", "market": "TSE"},  # Non-numeric
        {"symbol": "12345", "name": "Five Digits", "market": "TSE"},  # Too many digits
        {"name": "Missing Symbol", "market": "TSE"},  # Missing symbol
        {"symbol": "1101", "market": "TSE"},  # Missing name
        {"symbol": "1101", "name": "Missing Market"},  # Missing market
    ]


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response for testing."""
    from unittest.mock import Mock
    
    def create_mock_response(status_code=200, json_data=None, raise_for_status=False):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        
        if raise_for_status:
            import httpx
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=Mock(), response=mock_response
            )
        else:
            mock_response.raise_for_status = Mock()
        
        return mock_response
    
    return create_mock_response


@pytest.fixture(scope="session")
def test_database_url():
    """Test database URL for testing."""
    return "sqlite:///./test_stock.db"


@pytest.fixture
def clean_database(db_session):
    """Ensure clean database for each test."""
    # Clear all tables before each test
    from src.models.stock import Stock
    
    db_session.query(Stock).delete()
    db_session.commit()
    
    yield db_session
    
    # Clean up after test
    db_session.query(Stock).delete()
    db_session.commit()


@pytest.fixture
async def async_client():
    """Create async test client for testing async endpoints."""
    from httpx import AsyncClient
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac