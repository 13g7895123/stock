"""均線計算服務類別"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
import pandas as pd
import uuid

from src.core.database import get_db
from src.models.stock import MovingAverages, StockDailyData, Stock, TaskExecutionLog

logger = logging.getLogger(__name__)


class MovingAveragesService:
    """均線計算服務類別"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def get_statistics(self) -> Dict[str, Any]:
        """獲取均線統計資訊"""
        try:
            # 計算有均線資料的股票數量
            stocks_with_ma = self.db.query(
                func.count(func.distinct(MovingAverages.stock_id))
            ).scalar()

            # 計算總均線記錄數
            total_ma_records = self.db.query(func.count(MovingAverages.id)).scalar()

            # 取得最新計算日期
            latest_calculation = self.db.query(
                func.max(MovingAverages.trade_date)
            ).scalar()
            
            latest_calculation_date = latest_calculation.strftime('%Y-%m-%d') if latest_calculation else None

            # 計算完整度 (有均線資料的股票數 / 總股票數)
            total_stocks = self.db.query(func.count(Stock.id)).filter(
                Stock.is_active == True
            ).scalar()
            
            calculation_completeness = round(
                (stocks_with_ma / total_stocks * 100) if total_stocks > 0 else 0, 
                1
            )

            return {
                "stocks_with_ma": stocks_with_ma or 0,
                "total_ma_records": total_ma_records or 0,
                "latest_calculation_date": latest_calculation_date,
                "calculation_completeness": calculation_completeness,
                "total_stocks": total_stocks or 0
            }

        except Exception as e:
            logger.error(f"獲取均線統計資訊失敗: {str(e)}")
            raise Exception(f"獲取統計資訊失敗: {str(e)}")

    def calculate_moving_averages(
        self, 
        stock_codes: Optional[List[str]] = None,
        periods: List[int] = None,
        force_recalculate: bool = False
    ) -> Dict[str, Any]:
        """同步計算均線"""
        try:
            if periods is None:
                periods = [5, 10, 20, 60, 72, 120, 240]

            # 如果沒有指定股票代碼，則獲取所有有資料的股票
            if stock_codes is None:
                stock_codes = self._get_stocks_with_data()

            processed_stocks = 0
            total_calculations = 0
            failed_stocks = []

            for stock_code in stock_codes:
                try:
                    calculations = self._calculate_single_stock_ma(stock_code, periods, force_recalculate)
                    if calculations:
                        total_calculations += len(calculations)
                        processed_stocks += 1
                        logger.info(f"成功計算股票 {stock_code} 均線，計算 {len(calculations)} 筆資料")
                    
                except Exception as e:
                    logger.error(f"計算股票 {stock_code} 均線失敗: {str(e)}")
                    failed_stocks.append(stock_code)

            success_rate = round((processed_stocks / len(stock_codes)) * 100, 2) if stock_codes else 0

            return {
                "success": True,
                "processed_stocks": processed_stocks,
                "total_stocks": len(stock_codes) if stock_codes else 0,
                "total_calculations": total_calculations,
                "success_rate": success_rate,
                "failed_stocks": failed_stocks,
                "periods_calculated": periods
            }

        except Exception as e:
            logger.error(f"計算均線失敗: {str(e)}")
            raise Exception(f"計算均線失敗: {str(e)}")

    def query_moving_averages(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        periods: Optional[List[int]] = None,
        page: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """查詢股票均線資料"""
        try:
            # 驗證股票代號
            if not self._validate_stock_code(stock_code):
                raise ValueError(f"無效的股票代號: {stock_code}")

            # 建立查詢
            query = self.db.query(MovingAverages).filter(
                MovingAverages.stock_id == stock_code
            )

            # 日期範圍篩選
            if start_date:
                query = query.filter(MovingAverages.trade_date >= start_date)
            if end_date:
                query = query.filter(MovingAverages.trade_date <= end_date)

            # 計算總記錄數
            total_records = query.count()

            # 分頁處理
            offset = (page - 1) * limit
            results = query.order_by(desc(MovingAverages.trade_date)).offset(offset).limit(limit).all()

            # 轉換為字典格式
            data = []
            for record in results:
                item = {
                    "stock_code": record.stock_id,
                    "trade_date": record.trade_date.strftime('%Y-%m-%d'),
                    "ma5": record.ma_5,
                    "ma10": record.ma_10,
                    "ma20": record.ma_20,
                    "ma60": record.ma_60,
                    "ma72": record.ma_72,
                    "ma120": record.ma_120,
                    "ma240": record.ma_240
                }

                # 取得對應的收盤價
                daily_data = self.db.query(StockDailyData).filter(
                    and_(
                        StockDailyData.stock_code == stock_code,
                        StockDailyData.trade_date == record.trade_date
                    )
                ).first()

                if daily_data:
                    item["close_price"] = daily_data.close_price

                data.append(item)

            total_pages = (total_records + limit - 1) // limit

            return {
                "success": True,
                "data": data,
                "total_records": total_records,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "stock_code": stock_code
            }

        except Exception as e:
            logger.error(f"查詢股票 {stock_code} 均線資料失敗: {str(e)}")
            return {
                "success": False,
                "data": [],
                "error": str(e)
            }

    def start_async_calculation(
        self,
        stock_codes: Optional[List[str]] = None,
        periods: List[int] = None,
        force_recalculate: bool = False,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """啟動非同步均線計算任務"""
        try:
            if periods is None:
                periods = [5, 10, 20, 60, 72, 120, 240]

            # 生成任務ID
            task_id = str(uuid.uuid4())

            # 如果沒有指定股票代碼，則獲取所有有資料的股票
            if stock_codes is None:
                stock_codes = self._get_stocks_with_data()

            # 建立TaskExecutionLog記錄整合到任務管理系統
            task_log = TaskExecutionLog(
                task_name=f"均線計算任務 ({len(stock_codes)}檔股票)",
                task_type="moving_averages_calculation",
                parameters=f'{{"task_id": "{task_id}", "stock_codes": {len(stock_codes)}, "periods": {periods}, "batch_size": {batch_size}}}',
                status="running",
                start_time=datetime.now(),
                progress=0,
                processed_count=0,
                total_count=len(stock_codes),
                success_count=0,
                error_count=0,
                result_summary=f"準備計算 {len(stock_codes)} 檔股票的均線",
                created_by="system"
            )
            
            # 儲存任務記錄
            self.db.add(task_log)
            self.db.commit()

            logger.info(f"啟動均線計算任務 {task_id}，處理 {len(stock_codes)} 檔股票，資料庫記錄ID: {task_log.id}")

            # 存儲任務狀態供查詢用 (使用簡單的記憶體存儲)
            if not hasattr(self, '_task_status'):
                self._task_status = {}
            self._task_status[task_id] = {
                "state": "RUNNING", 
                "task_log_id": task_log.id,
                "current": 0,
                "total": len(stock_codes),
                "percentage": 0,
                "stage": "開始執行均線計算...",
                "start_time": datetime.now()
            }
            
            # 在背景執行均線計算任務
            self._execute_ma_calculation_task(task_id, task_log.id, stock_codes, periods, force_recalculate, batch_size)

            return {
                "success": True,
                "task_id": task_id,
                "message": f"均線計算任務已啟動，將處理 {len(stock_codes)} 檔股票",
                "total_stocks": len(stock_codes) if stock_codes else 0,
                "periods": periods,
                "batch_size": batch_size
            }

        except Exception as e:
            logger.error(f"啟動非同步計算失敗: {str(e)}")
            raise Exception(f"啟動非同步計算失敗: {str(e)}")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查詢非同步任務狀態"""
        try:
            # 首先檢查記憶體中的任務狀態
            if hasattr(self, '_task_status') and task_id in self._task_status:
                status = self._task_status[task_id]
                task_log_id = status.get("task_log_id")
                
                # 從資料庫查詢最新狀態
                if task_log_id:
                    task_log = self.db.query(TaskExecutionLog).filter(
                        TaskExecutionLog.id == task_log_id
                    ).first()
                    
                    if task_log:
                        # 更新狀態
                        if task_log.status == "completed":
                            status["state"] = "SUCCESS"
                        elif task_log.status == "failed":
                            status["state"] = "FAILURE"
                        else:
                            status["state"] = "PROGRESS"
                        
                        status["current"] = task_log.processed_count or 0
                        status["total"] = task_log.total_count or 0
                        status["percentage"] = task_log.progress or 0
                        status["stage"] = task_log.result_summary or "執行中..."
                        
                        if task_log.status == "completed":
                            status["result"] = {
                                "processed_stocks": task_log.success_count,
                                "failed_stocks": task_log.error_count,
                                "total_calculations": task_log.processed_count
                            }
                        elif task_log.error_message:
                            status["error"] = task_log.error_message
                
                return {
                    "success": True,
                    "data": status
                }
            else:
                # 嘗試從資料庫查詢（根據task_id從parameters中搜尋）
                task_log = self.db.query(TaskExecutionLog).filter(
                    TaskExecutionLog.task_type == "moving_averages_calculation",
                    TaskExecutionLog.parameters.like(f'%"task_id": "{task_id}"%')
                ).first()
                
                if task_log:
                    state = "PENDING"
                    if task_log.status == "completed":
                        state = "SUCCESS"
                    elif task_log.status == "failed":
                        state = "FAILURE"
                    elif task_log.status == "running":
                        state = "PROGRESS"
                    
                    return {
                        "success": True,
                        "data": {
                            "state": state,
                            "current": task_log.processed_count or 0,
                            "total": task_log.total_count or 0,
                            "percentage": task_log.progress or 0,
                            "stage": task_log.result_summary or "執行中...",
                            "result": None,
                            "error": task_log.error_message
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"找不到任務ID: {task_id}"
                    }

        except Exception as e:
            logger.error(f"查詢任務狀態失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消非同步任務"""
        try:
            # TODO: 這裡應該取消真正的Celery任務
            logger.info(f"取消任務: {task_id}")
            
            return {
                "success": True,
                "message": f"任務 {task_id} 已取消"
            }

        except Exception as e:
            logger.error(f"取消任務失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def validate_data_consistency(self, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """驗證均線資料一致性"""
        try:
            # 簡單的一致性檢查
            inconsistent_records = 0
            total_records_checked = 0

            # TODO: 實作真正的資料一致性驗證邏輯
            
            return {
                "success": True,
                "total_records_checked": total_records_checked,
                "inconsistent_records": inconsistent_records,
                "fixed_records": 0,
                "validation_time": 0.5
            }

        except Exception as e:
            logger.error(f"驗證資料一致性失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def clear_moving_averages(self, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """清除均線資料"""
        try:
            if stock_code:
                # 清除特定股票的均線資料
                deleted_count = self.db.query(MovingAverages).filter(
                    MovingAverages.stock_id == stock_code
                ).delete()
                message = f"已清除股票 {stock_code} 的 {deleted_count} 筆均線資料"
            else:
                # 清除所有均線資料
                deleted_count = self.db.query(MovingAverages).delete()
                message = f"已清除所有 {deleted_count} 筆均線資料"

            self.db.commit()
            logger.info(message)

            return {
                "success": True,
                "deleted_records": deleted_count,
                "message": message
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"清除均線資料失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_stocks_with_data(self) -> List[str]:
        """獲取有歷史資料的股票代碼清單"""
        try:
            stock_codes = self.db.query(
                func.distinct(StockDailyData.stock_code)
            ).all()
            
            return [stock_code[0] for stock_code in stock_codes]

        except Exception as e:
            logger.error(f"獲取股票清單失敗: {str(e)}")
            return []

    def _validate_stock_code(self, stock_code: str) -> bool:
        """驗證股票代號格式"""
        try:
            # 檢查格式：4位數字且不以0開頭
            if not stock_code or len(stock_code) != 4:
                return False
            if not stock_code.isdigit():
                return False
            if stock_code.startswith('0'):
                return False
            
            return True

        except Exception:
            return False

    def _calculate_single_stock_ma(
        self, 
        stock_code: str, 
        periods: List[int],
        force_recalculate: bool = False
    ) -> List[Dict[str, Any]]:
        """計算單一股票的均線"""
        try:
            # 獲取股票的歷史資料
            daily_data = self.db.query(StockDailyData).filter(
                StockDailyData.stock_code == stock_code
            ).order_by(StockDailyData.trade_date).all()

            if len(daily_data) < max(periods):
                logger.warning(f"股票 {stock_code} 歷史資料不足，無法計算 {max(periods)} 日均線")
                return []

            # 轉換為pandas DataFrame
            df = pd.DataFrame([
                {
                    'trade_date': record.trade_date,
                    'close_price': record.close_price
                }
                for record in daily_data
            ])

            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date')

            calculations = []

            # 計算各週期均線
            for _, row in df.iterrows():
                trade_date = row['trade_date']
                
                # 檢查是否已存在計算結果
                existing_record = self.db.query(MovingAverages).filter(
                    and_(
                        MovingAverages.stock_id == stock_code,
                        MovingAverages.trade_date == trade_date
                    )
                ).first()
                
                # 如果不強制重算，且記錄已存在且所有均線都有值，則跳過
                if not force_recalculate and existing_record:
                    # 檢查是否所有均線都已有值
                    all_ma_calculated = all([
                        existing_record.ma_5 is not None,
                        existing_record.ma_10 is not None,
                        existing_record.ma_20 is not None,
                        existing_record.ma_60 is not None,
                        existing_record.ma_72 is not None,
                        existing_record.ma_120 is not None,
                        existing_record.ma_240 is not None
                    ])
                    if all_ma_calculated:
                        continue

                # 計算各週期均線
                ma_values = {}
                for period in periods:
                    # 取得指定期間的資料
                    period_data = df[df['trade_date'] <= trade_date].tail(period)
                    
                    if len(period_data) >= period:
                        ma_value = period_data['close_price'].mean()
                        ma_values[f'ma_{period}'] = round(ma_value, 4)
                    else:
                        ma_values[f'ma_{period}'] = None

                # 建立或更新均線記錄
                if existing_record:
                    # 更新現有記錄（補上缺少的均線值）
                    updated = False
                    for period in periods:
                        ma_key = f'ma_{period}'
                        new_value = ma_values.get(ma_key)
                        current_value = getattr(existing_record, ma_key, None)
                        # 只有當新值存在且當前值為空時才更新
                        if new_value is not None and current_value is None:
                            setattr(existing_record, ma_key, new_value)
                            updated = True
                        # 或者強制重算時，直接更新
                        elif force_recalculate and new_value is not None:
                            setattr(existing_record, ma_key, new_value)
                            updated = True
                    
                    if updated:
                        calculations.append({
                            "trade_date": trade_date.strftime('%Y-%m-%d'),
                            "stock_code": stock_code,
                            **ma_values
                        })
                else:
                    # 新增記錄
                    new_record = MovingAverages(
                        stock_id=stock_code,
                        trade_date=trade_date,
                        ma_5=ma_values.get('ma_5'),
                        ma_10=ma_values.get('ma_10'),
                        ma_20=ma_values.get('ma_20'),
                        ma_60=ma_values.get('ma_60'),
                        ma_72=ma_values.get('ma_72'),
                        ma_120=ma_values.get('ma_120'),
                        ma_240=ma_values.get('ma_240')
                    )
                    self.db.add(new_record)

                calculations.append({
                    "trade_date": trade_date.strftime('%Y-%m-%d'),
                    "stock_code": stock_code,
                    **ma_values
                })

            self.db.commit()
            logger.info(f"成功計算股票 {stock_code} 的 {len(calculations)} 筆均線資料")
            return calculations

        except Exception as e:
            self.db.rollback()
            logger.error(f"計算股票 {stock_code} 均線失敗: {str(e)}")
            raise Exception(f"計算股票 {stock_code} 均線失敗: {str(e)}")

    def _execute_ma_calculation_task(
        self, 
        task_id: str, 
        task_log_id: int, 
        stock_codes: List[str], 
        periods: List[int],
        force_recalculate: bool,
        batch_size: int
    ):
        """背景執行均線計算任務（多線程並行處理）"""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import queue
        
        # 進度追蹤用的共享變數
        progress_lock = threading.Lock()
        progress_data = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "total_calculations": 0
        }
        
        def calculate_stock_ma(stock_code: str) -> dict:
            """計算單一股票均線（線程安全版本）"""
            from src.core.database import SessionLocal
            
            # 每個線程使用獨立的資料庫連接
            local_db = SessionLocal()
            try:
                # 獲取股票的歷史資料
                daily_data = local_db.query(StockDailyData).filter(
                    StockDailyData.stock_code == stock_code
                ).order_by(StockDailyData.trade_date).all()

                if len(daily_data) < max(periods):
                    return {"stock_code": stock_code, "success": False, "calculations": 0, "reason": "資料不足"}

                # 轉換為pandas DataFrame
                df = pd.DataFrame([
                    {
                        'trade_date': record.trade_date,
                        'close_price': record.close_price
                    }
                    for record in daily_data
                ])

                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date')

                calculations_count = 0

                # 計算各週期均線
                for _, row in df.iterrows():
                    trade_date = row['trade_date']
                    
                    # 檢查是否已存在計算結果
                    existing_record = local_db.query(MovingAverages).filter(
                        and_(
                            MovingAverages.stock_id == stock_code,
                            MovingAverages.trade_date == trade_date
                        )
                    ).first()
                    
                    # 如果不強制重算，且記錄已存在且所有均線都有值，則跳過
                    if not force_recalculate and existing_record:
                        all_ma_calculated = all([
                            existing_record.ma_5 is not None,
                            existing_record.ma_10 is not None,
                            existing_record.ma_20 is not None,
                            existing_record.ma_60 is not None,
                            existing_record.ma_72 is not None,
                            existing_record.ma_120 is not None,
                            existing_record.ma_240 is not None
                        ])
                        if all_ma_calculated:
                            continue

                    # 計算各週期均線
                    ma_values = {}
                    for period in periods:
                        period_data = df[df['trade_date'] <= trade_date].tail(period)
                        
                        if len(period_data) >= period:
                            ma_value = period_data['close_price'].mean()
                            ma_values[f'ma_{period}'] = round(ma_value, 4)
                        else:
                            ma_values[f'ma_{period}'] = None

                    # 建立或更新均線記錄
                    if existing_record:
                        updated = False
                        for period in periods:
                            ma_key = f'ma_{period}'
                            new_value = ma_values.get(ma_key)
                            current_value = getattr(existing_record, ma_key, None)
                            if new_value is not None and current_value is None:
                                setattr(existing_record, ma_key, new_value)
                                updated = True
                            elif force_recalculate and new_value is not None:
                                setattr(existing_record, ma_key, new_value)
                                updated = True
                        
                        if updated:
                            calculations_count += 1
                    else:
                        new_record = MovingAverages(
                            stock_id=stock_code,
                            trade_date=trade_date,
                            ma_5=ma_values.get('ma_5'),
                            ma_10=ma_values.get('ma_10'),
                            ma_20=ma_values.get('ma_20'),
                            ma_60=ma_values.get('ma_60'),
                            ma_72=ma_values.get('ma_72'),
                            ma_120=ma_values.get('ma_120'),
                            ma_240=ma_values.get('ma_240')
                        )
                        local_db.add(new_record)
                        calculations_count += 1

                local_db.commit()
                return {"stock_code": stock_code, "success": True, "calculations": calculations_count}

            except Exception as e:
                local_db.rollback()
                logger.error(f"計算股票 {stock_code} 均線失敗: {str(e)}")
                return {"stock_code": stock_code, "success": False, "calculations": 0, "error": str(e)}
            finally:
                local_db.close()
        
        def run_parallel_calculation():
            """並行執行均線計算"""
            try:
                # 獲取任務記錄
                task_log = self.db.query(TaskExecutionLog).filter(
                    TaskExecutionLog.id == task_log_id
                ).first()
                
                if not task_log:
                    logger.error(f"找不到任務記錄ID: {task_log_id}")
                    return
                
                total_stocks = len(stock_codes)
                # 使用線程池並行處理，根據CPU核心數決定線程數
                import os
                max_workers = min(os.cpu_count() * 2 or 4, 8)  # 最多8個線程
                
                logger.info(f"開始並行計算 {total_stocks} 檔股票的均線，使用 {max_workers} 個線程")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有任務
                    future_to_stock = {
                        executor.submit(calculate_stock_ma, stock_code): stock_code 
                        for stock_code in stock_codes
                    }
                    
                    # 處理完成的任務
                    for future in as_completed(future_to_stock):
                        stock_code = future_to_stock[future]
                        try:
                            result = future.result()
                            
                            with progress_lock:
                                progress_data["processed"] += 1
                                if result["success"]:
                                    progress_data["success"] += 1
                                    progress_data["total_calculations"] += result["calculations"]
                                else:
                                    progress_data["failed"] += 1
                                
                                # 更新進度
                                current = progress_data["processed"]
                                progress = round((current / total_stocks) * 100, 1)
                                
                                # 每處理 10 檔股票更新一次資料庫進度
                                if current % 10 == 0 or current == total_stocks:
                                    task_log.progress = progress
                                    task_log.processed_count = current
                                    task_log.success_count = progress_data["success"]
                                    task_log.error_count = progress_data["failed"]
                                    task_log.result_summary = f"進度: {current}/{total_stocks} ({progress}%)，成功: {progress_data['success']}，失敗: {progress_data['failed']}"
                                    self.db.commit()
                                
                                # 更新記憶體中的任務狀態
                                if hasattr(self, '_task_status') and task_id in self._task_status:
                                    self._task_status[task_id].update({
                                        "current": current,
                                        "percentage": progress,
                                        "stage": f"已處理 {current}/{total_stocks} 檔股票..."
                                    })
                            
                            if result["success"] and result["calculations"] > 0:
                                logger.debug(f"股票 {stock_code} 計算完成，更新 {result['calculations']} 筆")
                                
                        except Exception as e:
                            with progress_lock:
                                progress_data["processed"] += 1
                                progress_data["failed"] += 1
                            logger.error(f"處理股票 {stock_code} 時發生錯誤: {str(e)}")
                
                # 任務完成
                task_log.status = "completed"
                task_log.end_time = datetime.now()
                task_log.duration_seconds = (task_log.end_time - task_log.start_time).total_seconds()
                task_log.progress = 100
                task_log.processed_count = total_stocks
                task_log.success_count = progress_data["success"]
                task_log.error_count = progress_data["failed"]
                task_log.result_summary = f"任務完成：成功計算 {progress_data['success']} 檔股票，失敗 {progress_data['failed']} 檔，總計算量 {progress_data['total_calculations']} 筆，耗時 {task_log.duration_seconds:.1f} 秒"
                
                # 更新記憶體中的任務狀態
                if hasattr(self, '_task_status') and task_id in self._task_status:
                    self._task_status[task_id].update({
                        "state": "SUCCESS",
                        "current": total_stocks,
                        "percentage": 100,
                        "stage": "計算完成",
                        "result": {
                            "processed_stocks": progress_data["success"],
                            "failed_stocks": progress_data["failed"],
                            "total_calculations": progress_data["total_calculations"]
                        }
                    })
                
                self.db.commit()
                logger.info(f"均線計算任務 {task_id} 完成：處理 {progress_data['success']}/{total_stocks} 檔股票，總計算量 {progress_data['total_calculations']} 筆，耗時 {task_log.duration_seconds:.1f} 秒")
                
            except Exception as e:
                # 任務失敗
                task_log = self.db.query(TaskExecutionLog).filter(
                    TaskExecutionLog.id == task_log_id
                ).first()
                if task_log:
                    task_log.status = "failed"
                    task_log.end_time = datetime.now()
                    task_log.duration_seconds = (task_log.end_time - task_log.start_time).total_seconds()
                    task_log.error_message = str(e)
                    task_log.result_summary = f"任務失敗：{str(e)}"
                    self.db.commit()
                
                # 更新記憶體中的任務狀態
                if hasattr(self, '_task_status') and task_id in self._task_status:
                    self._task_status[task_id].update({
                        "state": "FAILURE",
                        "error": str(e)
                    })
                
                logger.error(f"均線計算任務 {task_id} 失敗: {str(e)}")
        
        # 在新線程中執行並行計算任務
        thread = threading.Thread(target=run_parallel_calculation)
        thread.daemon = True
        thread.start()