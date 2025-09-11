"""Concurrent stock data updater service with thread pool optimization."""

import asyncio
import concurrent.futures
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from src.models.stock import TaskExecutionLog
from src.services.task_execution_service import TaskExecutionService
from src.services.daily_data_service import DailyDataService

logger = logging.getLogger(__name__)


class ConcurrentStockUpdater:
    """Multi-threaded stock data updater service."""
    
    def __init__(
        self,
        db_session: Session,
        max_workers: int = 4,
        timeout_per_stock: float = 120.0,
        batch_size: int = 10
    ):
        """
        Initialize concurrent stock updater.
        
        Args:
            db_session: Database session
            max_workers: Maximum number of concurrent threads
            timeout_per_stock: Timeout per stock in seconds
            batch_size: Number of stocks to process in each batch
        """
        self.db_session = db_session
        self.max_workers = max_workers
        self.timeout_per_stock = timeout_per_stock
        self.batch_size = batch_size
        self.task_service = TaskExecutionService(db_session)
        
    async def update_stocks_concurrent(
        self,
        stock_codes: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        使用多執行續並行更新多檔股票資料
        
        Args:
            stock_codes: 股票代號清單
            progress_callback: 進度回調函數 (current, total, message)
        
        Returns:
            更新結果統計
        """
        start_time = time.time()
        
        # 啟動任務紀錄
        task_id = self.task_service.start_task(
            task_name="批次更新股票歷史資料",
            task_type="concurrent_stock_update",
            parameters={
                "stock_codes": stock_codes,
                "max_workers": self.max_workers,
                "timeout_per_stock": self.timeout_per_stock,
                "batch_size": self.batch_size
            },
            total_count=len(stock_codes),
            created_by="system"
        )
        
        try:
            results = {
                "task_id": task_id,
                "total_stocks": len(stock_codes),
                "successful_updates": 0,
                "failed_updates": 0,
                "skipped_updates": 0,
                "total_records_processed": 0,
                "total_records_created": 0,
                "total_records_updated": 0,
                "execution_time": 0,
                "successful_stocks": [],
                "failed_stocks": [],
                "skipped_stocks": [],
                "detailed_results": []
            }
            
            logger.info(f"Starting concurrent update for {len(stock_codes)} stocks with {self.max_workers} workers")
            
            # 分批處理股票
            batches = [stock_codes[i:i + self.batch_size] for i in range(0, len(stock_codes), self.batch_size)]
            processed_count = 0
            
            for batch_idx, batch in enumerate(batches):
                logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} with {len(batch)} stocks")
                
                # 使用線程池並行處理當前批次
                batch_results = await self._process_batch_concurrent(batch, task_id)
                
                # 統計批次結果
                for result in batch_results:
                    processed_count += 1
                    results["detailed_results"].append(result)
                    
                    if result["status"] == "success":
                        results["successful_updates"] += 1
                        results["successful_stocks"].append(result["stock_code"])
                        results["total_records_processed"] += result.get("records_processed", 0)
                        results["total_records_created"] += result.get("records_created", 0)
                        results["total_records_updated"] += result.get("records_updated", 0)
                    elif result["status"] == "skipped":
                        results["skipped_updates"] += 1
                        results["skipped_stocks"].append({
                            "stock_code": result["stock_code"],
                            "reason": result.get("reason", "Data already up to date"),
                            "latest_date": result.get("latest_date")
                        })
                    else:
                        results["failed_updates"] += 1
                        results["failed_stocks"].append({
                            "stock_code": result["stock_code"],
                            "error": result.get("error", "Unknown error")
                        })
                    
                    # 更新進度
                    progress = int((processed_count / len(stock_codes)) * 100)
                    self.task_service.update_progress(
                        task_id=task_id,
                        progress=progress,
                        processed_count=processed_count,
                        success_count=results["successful_updates"],
                        error_count=results["failed_updates"]
                    )
                    
                    # 調用進度回調
                    if progress_callback:
                        progress_callback(
                            processed_count,
                            len(stock_codes),
                            f"已處理 {result['stock_code']}"
                        )
                
                # 批次間短暫延遲，避免過度負載
                if batch_idx < len(batches) - 1:
                    await asyncio.sleep(1)
            
            # 計算總執行時間
            results["execution_time"] = time.time() - start_time
            
            # 完成任務紀錄
            success_rate = results["successful_updates"] / len(stock_codes) * 100 if len(stock_codes) > 0 else 0
            result_summary = (
                f"成功: {results['successful_updates']}, "
                f"跳過: {results['skipped_updates']}, "
                f"失敗: {results['failed_updates']}, "
                f"處理記錄: {results['total_records_processed']}, "
                f"成功率: {success_rate:.1f}%, "
                f"執行時間: {results['execution_time']:.1f}秒"
            )
            
            self.task_service.complete_task(
                task_id=task_id,
                status="completed",
                result_summary=result_summary
            )
            
            logger.info(f"Concurrent update completed: {result_summary}")
            return results
            
        except Exception as e:
            # 記錄任務失敗
            error_message = f"批次更新過程中發生錯誤: {str(e)}"
            self.task_service.complete_task(
                task_id=task_id,
                status="failed",
                error_message=error_message
            )
            logger.error(error_message)
            raise
    
    async def _process_batch_concurrent(self, stock_codes: List[str], task_id: int) -> List[Dict[str, Any]]:
        """使用線程池並行處理一批股票"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務到線程池
            future_to_stock = {
                executor.submit(self._update_single_stock, stock_code): stock_code
                for stock_code in stock_codes
            }
            
            results = []
            
            # 等待所有任務完成
            for future in as_completed(future_to_stock):
                stock_code = future_to_stock[future]
                try:
                    result = future.result(timeout=self.timeout_per_stock)
                    results.append(result)
                    logger.debug(f"Stock {stock_code} processed successfully")
                    
                except concurrent.futures.TimeoutError:
                    error_msg = f"Stock {stock_code} update timed out after {self.timeout_per_stock}s"
                    logger.warning(error_msg)
                    results.append({
                        "stock_code": stock_code,
                        "status": "failed",
                        "error": error_msg,
                        "records_processed": 0,
                        "records_created": 0,
                        "records_updated": 0
                    })
                    
                except Exception as e:
                    error_msg = f"Stock {stock_code} update failed: {str(e)}"
                    logger.error(error_msg)
                    results.append({
                        "stock_code": stock_code,
                        "status": "failed",
                        "error": error_msg,
                        "records_processed": 0,
                        "records_created": 0,
                        "records_updated": 0
                    })
            
            return results
    
    def _update_single_stock(self, stock_code: str) -> Dict[str, Any]:
        """更新單檔股票資料 (在線程中執行)"""
        try:
            logger.debug(f"Starting update for stock {stock_code}")
            
            # 創建新的資料庫會話（線程安全）
            from src.core.database import get_session_for_thread
            thread_db_session = get_session_for_thread()
            
            try:
                # 創建日線資料服務
                daily_service = DailyDataService(db_session=thread_db_session)
                
                # 同步調用日線資料更新
                import asyncio
                
                # 在線程中執行非同步函數
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # 使用智能跳過功能，但可以通過 force_update 參數強制更新
                    result = loop.run_until_complete(
                        daily_service.get_daily_data_for_stock(stock_code, force_update=False)
                    )
                finally:
                    loop.close()
                
                if result.get("status") == "success":
                    return {
                        "stock_code": stock_code,
                        "status": "success",
                        "records_processed": result.get("records_processed", 0),
                        "records_created": result.get("created", 0),
                        "records_updated": result.get("updated", 0),
                        "timestamp": result.get("timestamp")
                    }
                elif result.get("status") == "skipped":
                    return {
                        "stock_code": stock_code,
                        "status": "skipped",
                        "reason": result.get("reason", "Data already up to date"),
                        "latest_date": result.get("latest_date"),
                        "records_processed": 0,
                        "records_created": 0,
                        "records_updated": 0,
                        "timestamp": result.get("timestamp")
                    }
                else:
                    return {
                        "stock_code": stock_code,
                        "status": "failed",
                        "error": result.get("error", "Unknown error"),
                        "records_processed": 0,
                        "records_created": 0,
                        "records_updated": 0
                    }
                    
            finally:
                thread_db_session.close()
                
        except Exception as e:
            logger.error(f"Error updating stock {stock_code}: {str(e)}")
            return {
                "stock_code": stock_code,
                "status": "failed",
                "error": str(e),
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0
            }