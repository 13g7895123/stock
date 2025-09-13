"""循序批次股票資料更新服務

解決優化更新造成系統過載的問題，採用資源友善的循序處理方式：
1. 分批處理：將股票分成多個批次
2. 循序執行：避免併發衝突
3. 資源監控：監控系統資源，超載時暫停
4. 速率限制：防止被broker網站封鎖
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.models.stock import Stock, StockDailyData, TaskExecutionLog
from src.services.daily_data_service import DailyDataService
from src.services.task_execution_service import TaskExecutionService

logger = logging.getLogger(__name__)


class SequentialBatchUpdater:
    """循序批次股票資料更新服務"""

    def __init__(
        self,
        db_session: Session,
        batch_size: int = 477,  # 1908/4 = 477 檔每批
        delay_between_stocks: float = 0.5,  # 股票間延遲(秒)
        delay_between_batches: float = 10.0,  # 批次間延遲(秒)
        cpu_threshold: float = 80.0,  # CPU使用率閾值(%)
        memory_threshold: float = 85.0,  # 記憶體使用率閾值(%)
        auto_pause_on_overload: bool = True,  # 超載時自動暫停
        max_retry_per_stock: int = 3  # 每檔股票最大重試次數
    ):
        """初始化循序批次更新服務

        Args:
            db_session: 資料庫會話
            batch_size: 批次大小（每批處理的股票數）
            delay_between_stocks: 股票間延遲時間
            delay_between_batches: 批次間延遲時間
            cpu_threshold: CPU使用率閾值
            memory_threshold: 記憶體使用率閾值
            auto_pause_on_overload: 是否在系統過載時自動暫停
            max_retry_per_stock: 每檔股票最大重試次數
        """
        self.db_session = db_session
        self.batch_size = batch_size
        self.delay_between_stocks = delay_between_stocks
        self.delay_between_batches = delay_between_batches
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.auto_pause_on_overload = auto_pause_on_overload
        self.max_retry_per_stock = max_retry_per_stock
        self.task_service = TaskExecutionService(db_session)

        # 狀態控制
        self.is_paused = False
        self.should_stop = False

        logger.info(f"SequentialBatchUpdater 初始化完成:")
        logger.info(f"  - 批次大小: {batch_size} 檔")
        logger.info(f"  - 股票間延遲: {delay_between_stocks}秒")
        logger.info(f"  - 批次間延遲: {delay_between_batches}秒")
        logger.info(f"  - CPU閾值: {cpu_threshold}%")
        logger.info(f"  - 記憶體閾值: {memory_threshold}%")
        logger.info(f"  - 自動暫停: {'啟用' if auto_pause_on_overload else '關閉'}")

    def check_system_resources(self) -> Dict[str, Any]:
        """檢查系統資源使用情況"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            is_overloaded = (
                cpu_percent > self.cpu_threshold or
                memory_percent > self.memory_threshold
            )

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "available_memory_gb": memory.available / (1024**3),
                "is_overloaded": is_overloaded,
                "status": "overloaded" if is_overloaded else "normal"
            }
        except Exception as e:
            logger.error(f"檢查系統資源時發生錯誤: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "available_memory_gb": 0,
                "is_overloaded": False,
                "status": "unknown"
            }

    async def wait_if_overloaded(self) -> None:
        """如果系統過載則等待"""
        if not self.auto_pause_on_overload:
            return

        resources = self.check_system_resources()

        if resources["is_overloaded"]:
            logger.warning(
                f"系統資源過載 - CPU: {resources['cpu_percent']:.1f}%, "
                f"記憶體: {resources['memory_percent']:.1f}% - 暫停處理"
            )

            self.is_paused = True

            # 等待系統資源恢復正常
            while resources["is_overloaded"] and not self.should_stop:
                await asyncio.sleep(5)  # 每5秒檢查一次
                resources = self.check_system_resources()
                logger.info(f"等待系統資源恢復 - CPU: {resources['cpu_percent']:.1f}%, 記憶體: {resources['memory_percent']:.1f}%")

            self.is_paused = False
            logger.info("系統資源已恢復正常，繼續處理")

    def split_stocks_into_batches(self, stock_codes: List[str]) -> List[List[str]]:
        """將股票代碼分成批次"""
        batches = []
        for i in range(0, len(stock_codes), self.batch_size):
            batch = stock_codes[i:i + self.batch_size]
            batches.append(batch)

        logger.info(f"將 {len(stock_codes)} 檔股票分成 {len(batches)} 個批次")
        return batches

    async def process_single_stock(self, stock_code: str, retry_count: int = 0) -> Dict[str, Any]:
        """處理單檔股票資料"""
        try:
            logger.debug(f"開始處理股票 {stock_code}")

            # 使用現有的 DailyDataService
            daily_service = DailyDataService(db_session=self.db_session)
            result = await daily_service.get_daily_data_for_stock(stock_code)

            logger.debug(f"股票 {stock_code} 處理完成: {result.get('status', 'unknown')}")
            return result

        except Exception as e:
            error_msg = f"處理股票 {stock_code} 時發生錯誤: {str(e)}"
            logger.error(error_msg)

            # 重試機制
            if retry_count < self.max_retry_per_stock:
                logger.info(f"股票 {stock_code} 第 {retry_count + 1} 次重試")
                await asyncio.sleep(2)  # 重試前等待2秒
                return await self.process_single_stock(stock_code, retry_count + 1)
            else:
                return {
                    "status": "failed",
                    "stock_code": stock_code,
                    "error": error_msg,
                    "records_processed": 0,
                    "created": 0,
                    "updated": 0
                }

    async def process_batch(
        self,
        batch: List[str],
        batch_number: int,
        total_batches: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """處理單個批次的股票"""
        logger.info(f"開始處理批次 {batch_number}/{total_batches} ({len(batch)} 檔股票)")

        results = []

        for i, stock_code in enumerate(batch):
            # 檢查是否需要停止
            if self.should_stop:
                logger.info("收到停止信號，中斷批次處理")
                break

            # 檢查系統資源
            await self.wait_if_overloaded()

            # 處理股票
            result = await self.process_single_stock(stock_code)
            results.append(result)

            # 更新進度
            processed_in_batch = i + 1
            if progress_callback:
                progress_callback(
                    processed_in_batch,
                    len(batch),
                    f"批次 {batch_number}/{total_batches} - 已處理 {stock_code} ({result['status']})"
                )

            # 股票間延遲
            if processed_in_batch < len(batch):  # 不是最後一檔
                await asyncio.sleep(self.delay_between_stocks)

        logger.info(f"批次 {batch_number}/{total_batches} 處理完成")
        return results

    async def update_stocks_sequential(
        self,
        stock_codes: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """循序更新多檔股票 (主要入口點)"""
        start_time = time.time()

        # 創建任務紀錄
        task_id = self.task_service.start_task(
            task_name="循序批次更新股票資料",
            task_type="sequential_batch_update",
            parameters={
                "stock_codes_count": len(stock_codes),
                "batch_size": self.batch_size,
                "delay_between_stocks": self.delay_between_stocks,
                "delay_between_batches": self.delay_between_batches,
                "resource_monitoring": True
            },
            total_count=len(stock_codes),
            created_by="sequential_system"
        )

        try:
            # 分批處理
            batches = self.split_stocks_into_batches(stock_codes)

            # 初始化結果統計
            all_results = []
            successful_updates = 0
            failed_updates = 0
            total_records_processed = 0
            total_records_created = 0
            total_records_updated = 0

            logger.info(f"開始循序批次更新 {len(stock_codes)} 檔股票，分成 {len(batches)} 個批次")

            # 處理每個批次
            for batch_idx, batch in enumerate(batches):
                batch_number = batch_idx + 1

                logger.info(f"處理批次 {batch_number}/{len(batches)}")

                # 檢查系統資源
                await self.wait_if_overloaded()

                # 處理批次
                batch_results = await self.process_batch(
                    batch,
                    batch_number,
                    len(batches),
                    progress_callback
                )

                # 統計批次結果
                for result in batch_results:
                    all_results.append(result)

                    if result["status"] == "success":
                        successful_updates += 1
                        total_records_processed += result.get("records_processed", 0)
                        total_records_created += result.get("created", 0)
                        total_records_updated += result.get("updated", 0)
                    else:
                        failed_updates += 1

                # 更新任務進度
                overall_progress = int((batch_number / len(batches)) * 100)
                processed_count = sum(len(batches[i]) for i in range(batch_number))

                self.task_service.update_progress(
                    task_id=task_id,
                    progress=overall_progress,
                    processed_count=processed_count
                )

                # 批次間延遲（最後一批不需要）
                if batch_number < len(batches) and not self.should_stop:
                    logger.info(f"批次間休息 {self.delay_between_batches} 秒")
                    await asyncio.sleep(self.delay_between_batches)

            # 計算執行時間和性能指標
            execution_time = time.time() - start_time

            # 最終結果統計
            result = {
                "task_id": task_id,
                "update_type": "循序批次更新",
                "total_stocks": len(stock_codes),
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "total_records_processed": total_records_processed,
                "total_records_created": total_records_created,
                "total_records_updated": total_records_updated,
                "execution_time": execution_time,
                "batches_processed": len(batches),
                "batch_size": self.batch_size,
                "performance_metrics": {
                    "stocks_per_second": len(stock_codes) / execution_time if execution_time > 0 else 0,
                    "records_per_second": total_records_processed / execution_time if execution_time > 0 else 0,
                    "success_rate": (successful_updates / len(stock_codes)) * 100 if len(stock_codes) > 0 else 0,
                    "average_records_per_stock": total_records_processed / successful_updates if successful_updates > 0 else 0
                },
                "resource_impact": "低負載循序處理",
                "detailed_results": all_results
            }

            # 完成任務紀錄
            success_rate = result["successful_updates"] / len(stock_codes) * 100 if len(stock_codes) > 0 else 0
            result_summary = (
                f"循序批次更新完成 - "
                f"成功: {result['successful_updates']}, "
                f"失敗: {result['failed_updates']}, "
                f"處理記錄: {result['total_records_processed']}, "
                f"成功率: {success_rate:.1f}%, "
                f"執行時間: {execution_time:.1f}秒, "
                f"處理速度: {result['performance_metrics']['stocks_per_second']:.1f} 檔/秒"
            )

            self.task_service.complete_task(
                task_id=task_id,
                status="completed",
                result_summary=result_summary
            )

            logger.info(f"循序批次更新完成: {result_summary}")
            return result

        except Exception as e:
            # 記錄任務失敗
            error_message = f"循序批次更新失敗: {str(e)}"
            self.task_service.complete_task(
                task_id=task_id,
                status="failed",
                error_message=error_message
            )
            logger.error(error_message)
            raise

    def pause(self) -> None:
        """暫停處理"""
        self.is_paused = True
        logger.info("循序批次更新已暫停")

    def resume(self) -> None:
        """恢復處理"""
        self.is_paused = False
        logger.info("循序批次更新已恢復")

    def stop(self) -> None:
        """停止處理"""
        self.should_stop = True
        logger.info("循序批次更新收到停止信號")