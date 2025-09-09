#!/usr/bin/env python
"""Simple database connection test."""

import sys
import os
from sqlalchemy import create_engine, text

# Database connection URL
DATABASE_URL = "postgresql://stock_user:password@localhost:9221/stock_analysis"

def test_database_connection():
    """Test PostgreSQL database connection."""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT current_database(), version()'))
            row = result.fetchone()
            
            print("[SUCCESS] Database connection successful!")
            print(f"Database: {row[0]}")
            print(f"PostgreSQL: {row[1][:60]}...")
            
            # Test basic operations
            conn.execute(text('CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(50))'))
            conn.execute(text("INSERT INTO test_table (name) VALUES ('test') ON CONFLICT DO NOTHING"))
            
            result = conn.execute(text('SELECT COUNT(*) FROM test_table'))
            count = result.fetchone()[0]
            print(f"Test table record count: {count}")
            
            # Clean up
            conn.execute(text('DROP TABLE IF EXISTS test_table'))
            conn.commit()
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

def test_stock_service():
    """Test stock service database operations."""
    try:
        # Add the backend src to path
        backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
        sys.path.insert(0, backend_src)
        
        # Import the service
        from src.services.stock_list_service import StockListService
        from src.core.database import engine
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        try:
            # Create service instance
            service = StockListService(db_session=session)
            
            # Test validation function
            test_stock = {
                "symbol": "2330",
                "name": "台積電",
                "market": "TSE"
            }
            
            is_valid = service.validate_stock_data(test_stock)
            print(f"Stock validation test passed: {is_valid}")
            
            # Test filtering function
            test_stocks = [
                {"symbol": "2330", "name": "台積電", "market": "TSE"},
                {"symbol": "0050", "name": "ETF", "market": "TSE"},  # Should be filtered out
                {"symbol": "1101", "name": "台泥", "market": "TSE"},
            ]
            
            filtered = service.filter_valid_stocks(test_stocks)
            print(f"Stock filtering test passed: {len(filtered)} valid stocks from {len(test_stocks)} total")
            
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"[ERROR] Stock service test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== 股票分析系統資料庫測試 ===\n")
    
    # Test database connection
    db_success = test_database_connection()
    
    print("\n" + "="*50 + "\n")
    
    # Test stock service if database is working
    if db_success:
        service_success = test_stock_service()
    else:
        service_success = False
        print("[SKIP] Stock service test skipped due to database connection failure")
    
    print("\n=== 測試結果總結 ===")
    print(f"資料庫連線測試: {'成功' if db_success else '失敗'}")
    print(f"股票服務測試: {'成功' if service_success else '失敗'}")
    
    if db_success and service_success:
        print("\n[SUCCESS] 所有測試通過！資料庫服務已就緒，可以進行API測試。")
        print("\n可用的API端點測試：")
        print("1. POST http://localhost:9121/api/v1/sync/stocks/sync - 同步股票資料")
        print("2. GET http://localhost:9121/api/v1/sync/stocks/count - 查看股票統計")
        print("3. GET http://localhost:9121/api/v1/sync/stocks/validate/2330 - 驗證股票代號")
        
        exit(0)
    else:
        print("\n[ERROR] 部分測試失敗，請檢查設定。")
        exit(1)