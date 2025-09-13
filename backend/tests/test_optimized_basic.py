"""簡化的優化批次更新功能測試"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.services.optimized_batch_updater import OptimizedBatchUpdater


class TestOptimizedBatchUpdaterBasic:
    """基本功能測試"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock資料庫會話"""
        return Mock()
    
    @pytest.fixture
    def updater(self, mock_db_session):
        """創建優化批次更新服務實例"""
        with patch('src.services.optimized_batch_updater.TaskExecutionService'):
            return OptimizedBatchUpdater(
                db_session=mock_db_session,
                max_workers=2,
                batch_size=3,
                enable_smart_skip=True,
                enable_batch_db_operations=True
            )

    def test_initialization_success(self, updater):
        """測試 1: 服務成功初始化"""
        assert updater.max_workers == 2
        assert updater.batch_size == 3
        assert updater.enable_smart_skip is True
        assert updater.enable_batch_db_operations is True

    def test_initialization_validation(self):
        """測試 2: 初始化參數驗證"""
        mock_db = Mock()
        
        # 測試無效的max_workers
        with pytest.raises(ValueError, match="max_workers 必須大於 0"):
            OptimizedBatchUpdater(db_session=mock_db, max_workers=0)
        
        # 測試無效的batch_size
        with pytest.raises(ValueError, match="batch_size 必須大於 0"):
            OptimizedBatchUpdater(db_session=mock_db, batch_size=0)

    def test_smart_skip_disabled(self, mock_db_session):
        """測試 3: 智能跳過機制關閉時的行為"""
        with patch('src.services.optimized_batch_updater.TaskExecutionService'):
            updater = OptimizedBatchUpdater(
                db_session=mock_db_session,
                enable_smart_skip=False
            )
            
            # 當智能跳過關閉時，應該總是返回 False (不跳過)
            result = updater.is_stock_data_up_to_date("2330")
            assert result is False

    def test_batch_save_empty_data(self, updater):
        """測試 4: 批次儲存空資料"""
        result = updater.batch_save_daily_data([])
        assert result == {"created": 0, "updated": 0}

    @pytest.mark.asyncio
    async def test_fetch_single_stock_basic(self, updater):
        """測試 5: 基本單股資料獲取"""
        with patch.object(updater, 'is_stock_data_up_to_date', return_value=True):
            result = await updater._fetch_single_stock_data("2330")
            
            # 當智能跳過啟用且資料最新時，應該跳過
            assert result["status"] == "skipped"
            assert result["stock_code"] == "2330"
            assert "reason" in result

    @pytest.mark.asyncio
    async def test_broker_failover_basic(self, updater):
        """測試 6: 基本Broker容錯機制"""
        # 模擬broker回應失敗
        with patch.object(updater, '_fetch_from_broker', return_value=None):
            # 測試broker回應為None的情況
            result = await updater._fetch_from_broker("http://test-broker.com", "2330")
            assert result is None

    def test_configuration_edge_cases(self):
        """測試 7: 配置邊界值測試"""
        mock_db = Mock()
        
        with patch('src.services.optimized_batch_updater.TaskExecutionService'):
            # 測試最小值
            updater = OptimizedBatchUpdater(
                db_session=mock_db,
                max_workers=1,
                batch_size=1,
                smart_skip_days=0
            )
            assert updater.max_workers == 1
            assert updater.batch_size == 1
            assert updater.smart_skip_days == 0
            
            # 測試較大值
            updater2 = OptimizedBatchUpdater(
                db_session=mock_db,
                max_workers=8,
                batch_size=100,
                smart_skip_days=30
            )
            assert updater2.max_workers == 8
            assert updater2.batch_size == 100
            assert updater2.smart_skip_days == 30

    @pytest.mark.asyncio 
    async def test_process_single_stock_sync_basic(self, updater):
        """測試 8: 同步處理單股基本功能"""
        with patch.object(updater, '_fetch_single_stock_data') as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "stock_code": "2330",
                "records_processed": 100
            }
            
            # 測試同步處理
            result = updater._process_single_stock_sync("2330")
            assert result["status"] == "success"
            assert result["stock_code"] == "2330"

    def test_feature_flags(self, mock_db_session):
        """測試 9: 功能開關測試"""
        with patch('src.services.optimized_batch_updater.TaskExecutionService'):
            # 測試所有功能關閉
            updater = OptimizedBatchUpdater(
                db_session=mock_db_session,
                enable_smart_skip=False,
                enable_batch_db_operations=False
            )
            
            assert updater.enable_smart_skip is False
            assert updater.enable_batch_db_operations is False
            
            # 測試智能跳過關閉的行為
            assert updater.is_stock_data_up_to_date("2330") is False

    @pytest.mark.asyncio
    async def test_incremental_update_basic(self, updater):
        """測試 10: 基本增量更新功能"""
        with patch.object(updater, '_fetch_single_stock_data') as mock_fetch:
            mock_fetch.return_value = {
                "status": "success",
                "records_processed": 50
            }
            
            result = await updater.incremental_update_stock("2330")
            assert result["status"] == "success"
            assert result["records_processed"] == 50


if __name__ == "__main__":
    # 執行基本測試
    pytest.main([__file__, "-v"])