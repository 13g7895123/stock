"""TDD 測試：優化的批次更新功能

測試包含：
1. 高優先級：並行處理功能測試
2. 中優先級：批次資料庫操作測試  
3. 中優先級：智能增量更新測試
"""

import pytest
import asyncio
import time
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from src.services.optimized_batch_updater import OptimizedBatchUpdater
from src.models.stock import Stock, StockDailyData, TaskExecutionLog
from src.core.database import get_db


class TestOptimizedBatchUpdater:
    """優化批次更新服務測試"""
    
    @pytest.fixture
    def db_session(self):
        """測試資料庫會話"""
        engine = create_engine("sqlite:///:memory:")
        from src.models.stock import Base
        Base.metadata.create_all(engine)
        
        session = Session(engine)
        yield session
        session.close()
    
    @pytest.fixture
    def sample_stocks(self, db_session):
        """創建測試股票資料"""
        stocks = []
        for i in range(10):
            stock = Stock(
                stock_code=f"000{i}",
                stock_name=f"測試股票{i}",
                market="TSE" if i % 2 == 0 else "TPEx",
                is_active=True
            )
            stocks.append(stock)
            db_session.add(stock)
        
        db_session.commit()
        return stocks
    
    @pytest.fixture
    def updater(self, db_session):
        """創建優化批次更新服務實例"""
        return OptimizedBatchUpdater(
            db_session=db_session,
            max_workers=4,
            batch_size=5,
            enable_smart_skip=True,
            enable_batch_db_operations=True
        )

    def test_initialization(self, updater):
        """測試 1: 服務初始化"""
        assert updater.max_workers == 4
        assert updater.batch_size == 5
        assert updater.enable_smart_skip is True
        assert updater.enable_batch_db_operations is True
        assert updater.db_session is not None

    @pytest.mark.asyncio
    async def test_parallel_processing_performance(self, updater, sample_stocks):
        """測試 2: 並行處理性能測試 (高優先級)"""
        stock_codes = [stock.stock_code for stock in sample_stocks]
        
        # 模擬數據獲取函數
        async def mock_fetch_data(stock_code):
            await asyncio.sleep(0.1)  # 模擬網路延遲
            return {
                "status": "success",
                "records_processed": 100,
                "stock_code": stock_code
            }
        
        with patch.object(updater, '_fetch_single_stock_data', side_effect=mock_fetch_data):
            start_time = time.time()
            
            # 執行並行更新
            result = await updater.update_stocks_parallel(stock_codes)
            
            execution_time = time.time() - start_time
            
            # 驗證並行執行比序列執行快
            # 10檔股票 × 0.1秒 = 1秒 (序列)
            # 10檔股票 ÷ 4 workers × 0.1秒 = 0.25秒 (並行)
            assert execution_time < 0.5, f"並行執行時間應該 < 0.5秒，實際：{execution_time:.2f}秒"
            
            # 驗證所有股票都被處理
            assert result["total_stocks"] == 10
            assert result["successful_updates"] == 10
            assert result["failed_updates"] == 0

    @pytest.mark.asyncio
    async def test_batch_database_operations(self, updater, sample_stocks, db_session):
        """測試 3: 批次資料庫操作測試 (中優先級)"""
        stock_code = sample_stocks[0].stock_code
        
        # 創建大量測試資料 (300筆)
        daily_data = []
        base_date = date(2023, 1, 1)
        
        for i in range(300):
            trade_date = base_date + timedelta(days=i)
            daily_data.append({
                "stock_code": stock_code,
                "trade_date": datetime.combine(trade_date, datetime.min.time()),
                "open_price": 100.0 + i,
                "high_price": 105.0 + i,
                "low_price": 95.0 + i,
                "close_price": 102.0 + i,
                "volume": 1000 + i
            })
        
        # 測試批次儲存
        start_time = time.time()
        result = updater.batch_save_daily_data(daily_data)
        execution_time = time.time() - start_time
        
        # 驗證批次操作成功且速度快
        assert result["created"] == 300
        assert result["updated"] == 0
        assert execution_time < 1.0, f"批次儲存時間應該 < 1秒，實際：{execution_time:.2f}秒"
        
        # 驗證資料正確儲存
        saved_count = db_session.query(StockDailyData).filter(
            StockDailyData.stock_code == stock_code
        ).count()
        assert saved_count == 300

    @pytest.mark.asyncio
    async def test_smart_incremental_update(self, updater, sample_stocks, db_session):
        """測試 4: 智能增量更新測試 (中優先級)"""
        stock_code = sample_stocks[0].stock_code
        
        # 先添加一些歷史資料 (模擬已存在的資料)
        existing_date = datetime(2023, 12, 1)
        existing_data = StockDailyData(
            stock_code=stock_code,
            trade_date=existing_date,
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000,
            data_source="test",
            is_validated=True
        )
        db_session.add(existing_data)
        db_session.commit()
        
        # 測試智能跳過功能
        is_up_to_date = updater.is_stock_data_up_to_date(stock_code)
        
        # 如果資料在7天內，應該跳過
        days_diff = (date.today() - existing_date.date()).days
        if days_diff <= 7:
            assert is_up_to_date is True
        else:
            assert is_up_to_date is False
        
        # 測試增量更新 - 只更新缺失的日期範圍
        with patch.object(updater, '_fetch_single_stock_data') as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "records_processed": 5,
                "created": 5,
                "updated": 0
            }
            
            result = await updater.incremental_update_stock(stock_code)
            
            if is_up_to_date:
                # 資料最新，應該跳過
                assert result["status"] == "skipped"
                assert mock_fetch.called is False
            else:
                # 資料過舊，應該更新
                assert result["status"] == "success"
                assert mock_fetch.called is True

    @pytest.mark.asyncio
    async def test_broker_failover_strategy(self, updater):
        """測試 5: Broker容錯策略測試"""
        stock_code = "2330"
        
        # 模擬不同broker的回應
        broker_responses = [
            None,  # 第一個broker失敗
            None,  # 第二個broker失敗  
            {      # 第三個broker成功
                "status": "success",
                "records_processed": 100,
                "data": []
            }
        ]
        
        with patch.object(updater, '_fetch_from_broker', side_effect=broker_responses):
            result = await updater._fetch_single_stock_data(stock_code)
            
            # 應該成功獲取資料（使用第三個broker）
            assert result["status"] == "success"
            assert result["records_processed"] == 100

    @pytest.mark.asyncio 
    async def test_task_progress_tracking(self, updater, sample_stocks):
        """測試 6: 任務進度追蹤"""
        stock_codes = [stock.stock_code for stock in sample_stocks[:3]]
        
        progress_updates = []
        
        def progress_callback(current, total, message):
            progress_updates.append({
                "current": current,
                "total": total,
                "message": message,
                "timestamp": datetime.now()
            })
        
        with patch.object(updater, '_fetch_single_stock_data') as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "records_processed": 50
            }
            
            result = await updater.update_stocks_parallel(
                stock_codes,
                progress_callback=progress_callback
            )
            
            # 驗證進度追蹤正常運作
            assert len(progress_updates) >= 3  # 至少3次進度更新
            assert progress_updates[-1]["current"] == 3  # 最後進度應該是100%
            assert progress_updates[-1]["total"] == 3

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, updater, sample_stocks):
        """測試 7: 錯誤處理和恢復機制"""
        stock_codes = [stock.stock_code for stock in sample_stocks[:5]]
        
        # 模擬部分股票失敗的情況
        def mock_fetch_with_errors(stock_code):
            if stock_code in ["0001", "0003"]:  # 模擬這兩檔失敗
                raise Exception(f"網路連線錯誤: {stock_code}")
            return {
                "status": "success", 
                "records_processed": 100,
                "stock_code": stock_code
            }
        
        with patch.object(updater, '_fetch_single_stock_data', side_effect=mock_fetch_with_errors):
            result = await updater.update_stocks_parallel(stock_codes)
            
            # 驗證錯誤處理
            assert result["total_stocks"] == 5
            assert result["successful_updates"] == 3  # 3檔成功
            assert result["failed_updates"] == 2     # 2檔失敗
            assert len(result["failed_stocks"]) == 2
            
            # 驗證失敗股票資訊
            failed_codes = [item["stock_code"] for item in result["failed_stocks"]]
            assert "0001" in failed_codes
            assert "0003" in failed_codes

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, updater, sample_stocks):
        """測試 8: 性能基準測試"""
        stock_codes = [stock.stock_code for stock in sample_stocks]
        
        # 測試數據：10檔股票，每檔100筆資料
        mock_data = {
            "status": "success",
            "records_processed": 100,
            "execution_time": 0.05  # 50ms per stock
        }
        
        with patch.object(updater, '_fetch_single_stock_data', return_value=mock_data):
            start_time = time.time()
            result = await updater.update_stocks_parallel(stock_codes)
            total_time = time.time() - start_time
            
            # 性能基準驗證
            assert total_time < 1.0, f"10檔股票並行處理應該 < 1秒，實際：{total_time:.2f}秒"
            assert result["total_records_processed"] == 1000  # 10檔 × 100筆
            
            # 計算處理速度 (records per second)
            rps = result["total_records_processed"] / total_time
            assert rps > 1000, f"處理速度應該 > 1000 records/sec，實際：{rps:.0f}"

    def test_configuration_validation(self):
        """測試 9: 配置參數驗證"""
        # 測試無效的max_workers
        with pytest.raises(ValueError, match="max_workers 必須大於 0"):
            OptimizedBatchUpdater(
                db_session=Mock(),
                max_workers=0
            )
        
        # 測試無效的batch_size  
        with pytest.raises(ValueError, match="batch_size 必須大於 0"):
            OptimizedBatchUpdater(
                db_session=Mock(),
                max_workers=4,
                batch_size=0
            )

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, updater, sample_stocks):
        """測試 10: 記憶體使用優化"""
        stock_codes = [stock.stock_code for stock in sample_stocks]
        
        # 模擬大量資料處理
        large_dataset = {
            "status": "success",
            "records_processed": 1000,
            "data_size_mb": 5.0
        }
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch.object(updater, '_fetch_single_stock_data', return_value=large_dataset):
            result = await updater.update_stocks_parallel(stock_codes)
            
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            # 驗證記憶體使用在合理範圍內 (< 100MB for 10 stocks)
            assert memory_increase < 100, f"記憶體增加應該 < 100MB，實際：{memory_increase:.1f}MB"


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v", "--tb=short"])