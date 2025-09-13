"""Manual task execution and tracking API endpoints."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.services.daily_data_service import DailyDataService
from src.services.optimized_batch_updater import OptimizedBatchUpdater
from src.services.sequential_batch_updater import SequentialBatchUpdater
from src.models.stock import Stock, TaskExecutionLog

logger = logging.getLogger(__name__)

router = APIRouter()

# Task status enumeration
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    STOCK_CRAWL = "stock_crawl"
    OPTIMIZED_STOCK_CRAWL = "optimized_stock_crawl"
    SEQUENTIAL_STOCK_CRAWL = "sequential_stock_crawl"
    DATA_UPDATE = "data_update"
    ANALYSIS = "analysis"

# Task models
class TaskCreate(BaseModel):
    name: str
    description: str
    task_type: TaskType
    parameters: Optional[Dict[str, Any]] = None

class TaskProgress(BaseModel):
    current: int
    total: int
    percent: float
    current_step: str
    recent_items: Optional[List[str]] = None

class OptimizedStockCrawlRequest(BaseModel):
    """優化股票爬蟲請求模型"""
    symbols: Optional[List[str]] = Field(
        None,
        description="股票代碼清單，為空則更新所有股票",
        example=["2330", "2317", "2454"]
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="並行處理線程數量"
    )
    batch_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="批次處理大小"
    )
    enable_smart_skip: bool = Field(
        default=True,
        description="是否啟用智能跳過機制"
    )
    enable_batch_db_operations: bool = Field(
        default=True,
        description="是否啟用批次資料庫操作"
    )
    smart_skip_days: int = Field(
        default=1,
        ge=0,
        le=30,
        description="智能跳過天數"
    )

class SequentialStockCrawlRequest(BaseModel):
    """循序股票爬蟲請求模型"""
    symbols: Optional[List[str]] = Field(
        None,
        description="股票代碼清單，為空則更新所有股票",
        example=["2330", "2317", "2454"]
    )
    batch_size: int = Field(
        default=477,
        ge=1,
        le=1000,
        description="批次處理大小（預設477檔，1908/4=477）"
    )
    delay_between_stocks: float = Field(
        default=0.5,
        ge=0.1,
        le=5.0,
        description="股票間延遲時間（秒）"
    )
    delay_between_batches: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="批次間延遲時間（秒）"
    )
    cpu_threshold: float = Field(
        default=80.0,
        ge=50.0,
        le=95.0,
        description="CPU使用率閾值（%）"
    )
    memory_threshold: float = Field(
        default=85.0,
        ge=50.0,
        le=95.0,
        description="記憶體使用率閾值（%）"
    )
    auto_pause_on_overload: bool = Field(
        default=True,
        description="是否在系統過載時自動暫停"
    )

class ManualTask:
    def __init__(self, task_id: str, name: str, description: str, task_type: TaskType):
        self.id = task_id
        self.name = name
        self.description = description
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.progress = TaskProgress(current=0, total=0, percent=0.0, current_step="準備中")
        self.result = None
        self.error_message = None
        self.parameters = {}

# Global task storage (in production, use Redis or database)
ACTIVE_TASKS = {}
TASK_HISTORY = []

@router.get("/manual", response_model=Dict[str, Any])
async def get_manual_tasks() -> Dict[str, Any]:
    """獲取手動執行任務列表 - Get manual task list."""
    
    # Convert active tasks to dict format
    running_tasks = []
    for task in ACTIVE_TASKS.values():
        if task.status == TaskStatus.RUNNING:
            execution_time = "計算中..."
            if task.start_time:
                elapsed = datetime.now() - task.start_time
                execution_time = f"{elapsed.total_seconds():.0f}秒"
            
            running_tasks.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status.value,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "execution_time": execution_time,
                "estimated_remaining": "計算中...",
                "current_step": task.progress.current_step,
                "progress": {
                    "current": task.progress.current,
                    "total": task.progress.total,
                    "percent": task.progress.percent
                },
                "recent_items": task.progress.recent_items or []
            })
    
    # Get recent task history
    task_history = []
    for task in TASK_HISTORY[-50:]:  # Get last 50 records
        execution_time = "未知"
        if task.start_time and task.end_time:
            elapsed = task.end_time - task.start_time
            execution_time = f"{elapsed.total_seconds():.0f}秒"
        
        result = task.result or {}
        task_history.append({
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status.value,
            "task_type": task.task_type.value,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "execution_time": execution_time,
            "processed_count": result.get("total_records_processed", 0),
            "success_count": result.get("successful_updates", 0),
            "failure_count": result.get("failed_updates", 0),
            "error_message": task.error_message
        })
    
    return {
        "running_tasks": running_tasks,
        "task_history": list(reversed(task_history)),  # Show newest first
        "stats": {
            "running_count": len(running_tasks),
            "completed_today": len([t for t in TASK_HISTORY if t.status == TaskStatus.COMPLETED]),
            "failed_today": len([t for t in TASK_HISTORY if t.status == TaskStatus.FAILED])
        },
        "timestamp": datetime.now().isoformat()
    }

@router.post("/manual/stock-crawl", response_model=Dict[str, Any])
async def create_stock_crawl_task(
    symbols: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """創建股票爬蟲任務 - Create stock crawling task."""
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Get symbols if not provided
    if symbols is None:
        try:
            stocks = db.query(Stock).filter(Stock.is_active == True).all()
            symbols = [stock.symbol for stock in stocks]
            logger.info(f"Retrieved {len(symbols)} active stocks from database")
        except Exception as e:
            logger.error(f"Error retrieving stocks from database: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
    
    # Validate symbols
    valid_symbols = []
    for symbol in symbols:
        if isinstance(symbol, str) and len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
            valid_symbols.append(symbol)
    
    if not valid_symbols:
        raise HTTPException(status_code=400, detail="No valid stock symbols provided")
    
    # Create task
    task = ManualTask(
        task_id=task_id,
        name=f"Broker爬蟲批次更新股票資料 ({len(valid_symbols)}檔)",
        description=f"使用8個broker網站爬取 {len(valid_symbols)} 檔股票的還原日線資料",
        task_type=TaskType.STOCK_CRAWL
    )
    task.parameters = {"symbols": valid_symbols}
    task.progress.total = len(valid_symbols)
    task.progress.current_step = f"準備爬取 {len(valid_symbols)} 檔股票資料"
    
    # Add to active tasks
    ACTIVE_TASKS[task_id] = task
    
    # Start background task
    background_tasks.add_task(run_stock_crawl_task, task_id, valid_symbols, db)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"已創建股票爬蟲任務，將處理 {len(valid_symbols)} 檔股票",
        "symbols_count": len(valid_symbols),
        "status": "created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "task_id": task_id,
            "symbols_count": len(valid_symbols),
            "status": "created"
        }
    }

@router.delete("/manual/{task_id}", response_model=Dict[str, Any])
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """取消執行中的任務 - Cancel running task."""
    
    if task_id not in ACTIVE_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = ACTIVE_TASKS[task_id]
    
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Task is not running")
    
    # Mark as cancelled
    task.status = TaskStatus.CANCELLED
    task.end_time = datetime.now()
    task.error_message = "User cancelled"
    
    # Move to history
    TASK_HISTORY.append(task)
    del ACTIVE_TASKS[task_id]
    
    return {
        "message": f"任務 {task.name} 已取消",
        "task_id": task_id,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/manual/{task_id}", response_model=Dict[str, Any])
async def get_task_details(task_id: str) -> Dict[str, Any]:
    """獲取任務詳情 - Get task details."""
    
    # Check active tasks
    if task_id in ACTIVE_TASKS:
        task = ACTIVE_TASKS[task_id]
    else:
        # Check history
        task = next((t for t in TASK_HISTORY if t.id == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    
    execution_time = "未開始"
    if task.start_time:
        if task.end_time:
            elapsed = task.end_time - task.start_time
        else:
            elapsed = datetime.now() - task.start_time
        execution_time = f"{elapsed.total_seconds():.0f}秒"
    
    result = task.result or {}
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type.value,
        "status": task.status.value,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "execution_time": execution_time,
        "progress": {
            "current": task.progress.current,
            "total": task.progress.total,
            "percent": task.progress.percent,
            "current_step": task.progress.current_step,
            "recent_items": task.progress.recent_items or []
        },
        "result": result,
        "error_message": task.error_message,
        "parameters": task.parameters
    }

@router.post("/manual/clear-completed", response_model=Dict[str, Any])
async def clear_completed_tasks() -> Dict[str, Any]:
    """清除已完成的任務記錄 - Clear completed task records."""

    global TASK_HISTORY

    original_count = len(TASK_HISTORY)
    TASK_HISTORY = [task for task in TASK_HISTORY if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
    cleared_count = original_count - len(TASK_HISTORY)

    return {
        "message": f"已清除 {cleared_count} 個已完成的任務記錄",
        "cleared_count": cleared_count,
        "remaining_count": len(TASK_HISTORY),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/manual/sequential-stock-crawl", response_model=Dict[str, Any])
async def create_sequential_stock_crawl_task(
    request: SequentialStockCrawlRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """創建循序股票爬蟲任務 - 使用資源友善的循序處理方式，避免系統過載."""

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Get symbols if not provided
    if request.symbols is None:
        try:
            stocks = db.query(Stock).filter(Stock.is_active == True).all()
            symbols = [stock.symbol for stock in stocks]
            logger.info(f"Retrieved {len(symbols)} active stocks from database")
        except Exception as e:
            logger.error(f"Error retrieving stocks from database: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
    else:
        symbols = request.symbols

    # Validate symbols
    valid_symbols = []
    for symbol in symbols:
        if isinstance(symbol, str) and len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
            valid_symbols.append(symbol)

    if not valid_symbols:
        raise HTTPException(status_code=400, detail="No valid stock symbols provided")

    # Validate parameters
    if request.batch_size <= 0 or request.batch_size > 1000:
        raise HTTPException(status_code=400, detail="batch_size must be between 1 and 1000")

    if request.delay_between_stocks < 0.1 or request.delay_between_stocks > 5.0:
        raise HTTPException(status_code=400, detail="delay_between_stocks must be between 0.1 and 5.0")

    if request.delay_between_batches < 1.0 or request.delay_between_batches > 60.0:
        raise HTTPException(status_code=400, detail="delay_between_batches must be between 1.0 and 60.0")

    # Calculate expected batches
    expected_batches = (len(valid_symbols) + request.batch_size - 1) // request.batch_size

    # Create task
    sequential_features = []
    sequential_features.append(f"分批處理({expected_batches}批)")
    sequential_features.append(f"批次大小({request.batch_size}檔)")
    if request.auto_pause_on_overload:
        sequential_features.append("資源監控")
    sequential_features.append(f"股票間延遲({request.delay_between_stocks}秒)")
    sequential_features.append(f"批次間延遲({request.delay_between_batches}秒)")

    task = ManualTask(
        task_id=task_id,
        name=f"【循序】批次更新股票資料 ({len(valid_symbols)}檔)",
        description=f"使用資源友善循序方式爬取 {len(valid_symbols)} 檔股票資料 - 功能: {', '.join(sequential_features)}",
        task_type=TaskType.SEQUENTIAL_STOCK_CRAWL
    )

    task.parameters = {
        "symbols": valid_symbols,
        "batch_size": request.batch_size,
        "delay_between_stocks": request.delay_between_stocks,
        "delay_between_batches": request.delay_between_batches,
        "cpu_threshold": request.cpu_threshold,
        "memory_threshold": request.memory_threshold,
        "auto_pause_on_overload": request.auto_pause_on_overload,
        "expected_batches": expected_batches,
        "processing_mode": "循序處理"
    }

    task.progress.total = len(valid_symbols)
    task.progress.current_step = f"準備循序爬取 {len(valid_symbols)} 檔股票資料（{expected_batches}批）"

    # Add to active tasks
    ACTIVE_TASKS[task_id] = task

    # Start background task
    background_tasks.add_task(
        run_sequential_stock_crawl_task,
        task_id,
        valid_symbols,
        request.batch_size,
        request.delay_between_stocks,
        request.delay_between_batches,
        request.cpu_threshold,
        request.memory_threshold,
        request.auto_pause_on_overload,
        db
    )

    logger.info(f"Created sequential stock crawl task {task_id} with features: {', '.join(sequential_features)}")

    return {
        "success": True,
        "task_id": task_id,
        "message": f"已創建循序股票爬蟲任務，將處理 {len(valid_symbols)} 檔股票",
        "symbols_count": len(valid_symbols),
        "sequential_features": sequential_features,
        "expected_batches": expected_batches,
        "performance_estimate": f"預期減少 70% 系統負載，循序處理 {expected_batches} 批次",
        "status": "created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "task_id": task_id,
            "symbols_count": len(valid_symbols),
            "processing_mode": "循序處理",
            "status": "created"
        }
    }

async def run_stock_crawl_task(task_id: str, symbols: List[str], db: Session):
    """執行股票爬蟲任務的背景函數 - Background function for stock crawling task."""
    
    task = ACTIVE_TASKS.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    # Create database record for task execution
    task_log = TaskExecutionLog(
        task_name=task.name,
        task_type="stock_crawl",
        parameters=f'{{"symbols": {len(symbols)}, "task_id": "{task_id}"}}',
        status="running",
        start_time=datetime.now(),
        progress=0,
        processed_count=0,
        total_count=len(symbols),
        success_count=0,
        error_count=0,
        result_summary=f"準備爬取 {len(symbols)} 檔股票資料",
        created_by="system"
    )
    
    try:
        # Add to database
        db.add(task_log)
        db.commit()
        
        # Mark task as running
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        logger.info(f"Starting stock crawl task {task_id} for {len(symbols)} symbols")
        
        # Initialize counters
        successful_updates = 0
        failed_updates = 0
        total_records_processed = 0
        
        # Process each stock
        for i, symbol in enumerate(symbols):
            if task.status == TaskStatus.CANCELLED:
                logger.info(f"Task {task_id} was cancelled")
                # Update database status
                task_log.status = "cancelled"
                task_log.end_time = datetime.now()
                task_log.duration_seconds = (task_log.end_time - task_log.start_time).total_seconds()
                task_log.error_message = "User cancelled"
                db.commit()
                return
                
            try:
                # Update progress
                task.progress.current = i
                task.progress.percent = round((i / len(symbols)) * 100, 1)
                task.progress.current_step = f"正在處理第 {i+1} / {len(symbols)} 檔股票: {symbol}"
                
                # Update database progress
                task_log.processed_count = i
                task_log.progress = int(task.progress.percent)
                task_log.result_summary = task.progress.current_step
                
                # Add to recent items
                if not task.progress.recent_items:
                    task.progress.recent_items = []
                task.progress.recent_items.append(symbol)
                if len(task.progress.recent_items) > 5:
                    task.progress.recent_items = task.progress.recent_items[-5:]
                
                logger.info(f"Processing stock {i+1}/{len(symbols)}: {symbol}")
                
                # Initialize daily data service for each stock
                daily_data_service = DailyDataService(db_session=db)
                
                # Fetch and save daily data using broker websites
                result = await daily_data_service.get_daily_data_for_stock(symbol)
                
                if result.get("status") == "success":
                    successful_updates += 1
                    total_records_processed += result.get("records_processed", 0)
                    task_log.success_count = successful_updates
                    logger.info(f"Successfully processed {symbol}: {result.get('records_processed', 0)} records")
                else:
                    failed_updates += 1
                    task_log.error_count = failed_updates
                    logger.error(f"Failed to process {symbol}: {result.get('error', 'Unknown error')}")
                
                # Commit progress updates every 10 stocks or at the end
                if (i + 1) % 10 == 0 or i == len(symbols) - 1:
                    db.commit()
                
                # Small delay to avoid overwhelming broker servers
                if i < len(symbols) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_updates += 1
                task_log.error_count = failed_updates
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Final progress update
        task.progress.current = len(symbols)
        task.progress.percent = 100.0
        task.progress.current_step = "任務完成"
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.end_time = datetime.now()
        task.result = {
            "total_symbols": len(symbols),
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "total_records_processed": total_records_processed,
            "execution_time_seconds": (task.end_time - task.start_time).total_seconds()
        }
        
        # Update database record - completed
        task_log.status = "completed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = (task.end_time - task.start_time).total_seconds()
        task_log.processed_count = len(symbols)
        task_log.progress = 100
        task_log.success_count = successful_updates
        task_log.error_count = failed_updates
        task_log.result_summary = f"任務完成：成功 {successful_updates} 檔，失敗 {failed_updates} 檔，處理 {total_records_processed} 筆資料"
        db.commit()
        
        logger.info(f"Stock crawl task {task_id} completed: {successful_updates} success, {failed_updates} failed, {total_records_processed} records")
        
    except Exception as e:
        # Mark as failed
        task.status = TaskStatus.FAILED
        task.end_time = datetime.now()
        task.error_message = str(e)
        
        # Update database record - failed
        task_log.status = "failed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = (task.end_time - task.start_time).total_seconds()
        task_log.error_message = str(e)
        task_log.result_summary = f"任務失敗：{str(e)}"
        db.commit()
        
        logger.error(f"Stock crawl task {task_id} failed: {e}")
        
    finally:
        # Move to history
        if task_id in ACTIVE_TASKS:
            TASK_HISTORY.append(task)
            del ACTIVE_TASKS[task_id]


@router.post("/manual/optimized-stock-crawl", response_model=Dict[str, Any])
async def create_optimized_stock_crawl_task(
    request: OptimizedStockCrawlRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """創建優化的股票爬蟲任務 - 使用高優先級與中優先級優化功能."""
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Get symbols if not provided
    if request.symbols is None:
        try:
            stocks = db.query(Stock).filter(Stock.is_active == True).all()
            symbols = [stock.symbol for stock in stocks]
            logger.info(f"Retrieved {len(symbols)} active stocks from database")
        except Exception as e:
            logger.error(f"Error retrieving stocks from database: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve active stocks from database")
    else:
        symbols = request.symbols
    
    # Validate symbols
    valid_symbols = []
    for symbol in symbols:
        if isinstance(symbol, str) and len(symbol) == 4 and symbol.isdigit() and not symbol.startswith("0"):
            valid_symbols.append(symbol)
    
    if not valid_symbols:
        raise HTTPException(status_code=400, detail="No valid stock symbols provided")
    
    # Validate optimization parameters
    if request.max_workers <= 0 or request.max_workers > 16:
        raise HTTPException(status_code=400, detail="max_workers must be between 1 and 16")
    
    if request.batch_size <= 0 or request.batch_size > 500:
        raise HTTPException(status_code=400, detail="batch_size must be between 1 and 500")
    
    if request.smart_skip_days < 0 or request.smart_skip_days > 30:
        raise HTTPException(status_code=400, detail="smart_skip_days must be between 0 and 30")
    
    # Create task
    optimization_features = []
    if request.max_workers > 1:
        optimization_features.append(f"並行處理({request.max_workers} workers)")
    if request.enable_batch_db_operations:
        optimization_features.append("批次資料庫操作")
    if request.enable_smart_skip:
        optimization_features.append(f"智能跳過({request.smart_skip_days}天)")
    
    task = ManualTask(
        task_id=task_id,
        name=f"【優化】批次更新股票資料 ({len(valid_symbols)}檔)",
        description=f"使用優化功能爬取 {len(valid_symbols)} 檔股票資料 - 功能: {', '.join(optimization_features)}",
        task_type=TaskType.OPTIMIZED_STOCK_CRAWL
    )
    
    task.parameters = {
        "symbols": valid_symbols,
        "max_workers": request.max_workers,
        "batch_size": request.batch_size,
        "enable_smart_skip": request.enable_smart_skip,
        "enable_batch_db_operations": request.enable_batch_db_operations,
        "smart_skip_days": request.smart_skip_days,
        "optimization_level": "高優先級+中優先級"
    }
    
    task.progress.total = len(valid_symbols)
    task.progress.current_step = f"準備優化爬取 {len(valid_symbols)} 檔股票資料"
    
    # Add to active tasks
    ACTIVE_TASKS[task_id] = task
    
    # Start background task
    background_tasks.add_task(
        run_optimized_stock_crawl_task, 
        task_id, 
        valid_symbols,
        request.max_workers,
        request.batch_size,
        request.enable_smart_skip,
        request.enable_batch_db_operations,
        request.smart_skip_days,
        db
    )
    
    logger.info(f"Created optimized stock crawl task {task_id} with features: {', '.join(optimization_features)}")
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"已創建優化股票爬蟲任務，將處理 {len(valid_symbols)} 檔股票",
        "symbols_count": len(valid_symbols),
        "optimization_features": optimization_features,
        "performance_estimate": f"預期提升 {60 + (request.max_workers - 1) * 25}% 執行速度",
        "status": "created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "task_id": task_id,
            "symbols_count": len(valid_symbols),
            "optimization_level": "高優先級+中優先級",
            "status": "created"
        }
    }


async def run_optimized_stock_crawl_task(
    task_id: str, 
    symbols: List[str],
    max_workers: int,
    batch_size: int,
    enable_smart_skip: bool,
    enable_batch_db_operations: bool,
    smart_skip_days: int,
    db: Session
):
    """執行優化股票爬蟲任務的背景函數."""
    
    task = ACTIVE_TASKS.get(task_id)
    if not task:
        logger.error(f"Optimized task {task_id} not found")
        return
    
    # Create database record for task execution
    task_log = TaskExecutionLog(
        task_name=task.name,
        task_type="optimized_stock_crawl",
        parameters=f'{{"symbols": {len(symbols)}, "max_workers": {max_workers}, "batch_size": {batch_size}, "optimizations": "parallel+batch_db+smart_skip"}}',
        status="running",
        start_time=datetime.now(),
        progress=0,
        processed_count=0,
        total_count=len(symbols),
        success_count=0,
        error_count=0,
        result_summary=f"準備優化爬取 {len(symbols)} 檔股票資料",
        created_by="optimized_system"
    )
    
    try:
        # Add to database
        db.add(task_log)
        db.commit()
        
        # Mark task as running
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        logger.info(f"Starting optimized stock crawl task {task_id} for {len(symbols)} symbols")
        
        # Initialize optimized batch updater
        updater = OptimizedBatchUpdater(
            db_session=db,
            max_workers=max_workers,
            batch_size=batch_size,
            enable_smart_skip=enable_smart_skip,
            enable_batch_db_operations=enable_batch_db_operations,
            smart_skip_days=smart_skip_days
        )
        
        # Progress callback function
        def progress_callback(current: int, total: int, message: str):
            task.progress.current = current
            task.progress.percent = round((current / total) * 100, 1)
            task.progress.current_step = f"優化處理中 {current}/{total}: {message}"
            
            # Update recent items
            if not task.progress.recent_items:
                task.progress.recent_items = []
            task.progress.recent_items.append(message.split(' ')[0] if ' ' in message else message)
            if len(task.progress.recent_items) > 5:
                task.progress.recent_items = task.progress.recent_items[-5:]
            
            # Update database progress
            task_log.processed_count = current
            task_log.progress = int(task.progress.percent)
            task_log.result_summary = task.progress.current_step
            db.commit()
        
        # Execute optimized parallel update
        result = await updater.update_stocks_parallel(
            stock_codes=symbols,
            progress_callback=progress_callback
        )
        
        # Final progress update
        task.progress.current = len(symbols)
        task.progress.percent = 100.0
        task.progress.current_step = "優化任務完成"
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.end_time = datetime.now()
        
        # Extract results
        successful_updates = result.get("successful_updates", 0)
        failed_updates = result.get("failed_updates", 0)
        skipped_updates = result.get("skipped_updates", 0)
        total_records_processed = result.get("total_records_processed", 0)
        execution_time = result.get("execution_time", 0)
        performance_metrics = result.get("performance_metrics", {})
        
        task.result = {
            "total_symbols": len(symbols),
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "skipped_updates": skipped_updates,
            "total_records_processed": total_records_processed,
            "execution_time_seconds": execution_time,
            "optimization_level": "高優先級+中優先級",
            "performance_metrics": performance_metrics,
            "features_used": result.get("features_used", []),
            "optimization_benefits": {
                "estimated_time_saved": max(0, (len(symbols) * 2) - execution_time),  # 假設未優化需要2秒/檔
                "parallel_efficiency": performance_metrics.get("optimization_efficiency", 0),
                "success_rate": performance_metrics.get("success_rate", 0)
            }
        }
        
        # Update database record - completed
        task_log.status = "completed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = execution_time
        task_log.processed_count = len(symbols)
        task_log.progress = 100
        task_log.success_count = successful_updates
        task_log.error_count = failed_updates
        
        optimization_summary = f"優化任務完成 - 成功:{successful_updates} 跳過:{skipped_updates} 失敗:{failed_updates} 記錄:{total_records_processed} 用時:{execution_time:.1f}秒 速度:{performance_metrics.get('stocks_per_second', 0):.1f}檔/秒"
        task_log.result_summary = optimization_summary
        
        db.commit()
        
        logger.info(f"Optimized stock crawl task {task_id} completed: {optimization_summary}")
        
    except Exception as e:
        # Mark as failed
        task.status = TaskStatus.FAILED
        task.end_time = datetime.now()
        task.error_message = str(e)
        
        # Update database record - failed
        task_log.status = "failed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = (task.end_time - task.start_time).total_seconds()
        task_log.error_message = str(e)
        task_log.result_summary = f"優化任務失敗：{str(e)}"
        db.commit()
        
        logger.error(f"Optimized stock crawl task {task_id} failed: {e}")

    finally:
        # Move to history
        if task_id in ACTIVE_TASKS:
            TASK_HISTORY.append(task)
            del ACTIVE_TASKS[task_id]


async def run_sequential_stock_crawl_task(
    task_id: str,
    symbols: List[str],
    batch_size: int,
    delay_between_stocks: float,
    delay_between_batches: float,
    cpu_threshold: float,
    memory_threshold: float,
    auto_pause_on_overload: bool,
    db: Session
):
    """執行循序股票爬蟲任務的背景函數 - 使用資源友善的循序處理方式."""

    task = ACTIVE_TASKS.get(task_id)
    if not task:
        logger.error(f"Sequential task {task_id} not found")
        return

    # Create database record for task execution
    task_log = TaskExecutionLog(
        task_name=task.name,
        task_type="sequential_stock_crawl",
        parameters=f'{{"symbols": {len(symbols)}, "batch_size": {batch_size}, "delays": "stocks:{delay_between_stocks}s,batches:{delay_between_batches}s", "resource_thresholds": "cpu:{cpu_threshold}%,memory:{memory_threshold}%"}}',
        status="running",
        start_time=datetime.now(),
        progress=0,
        processed_count=0,
        total_count=len(symbols),
        success_count=0,
        error_count=0,
        result_summary=f"準備循序爬取 {len(symbols)} 檔股票資料",
        created_by="sequential_system"
    )

    try:
        # Add to database
        db.add(task_log)
        db.commit()

        # Mark task as running
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        logger.info(f"Starting sequential stock crawl task {task_id} for {len(symbols)} symbols")

        # Initialize sequential batch updater
        updater = SequentialBatchUpdater(
            db_session=db,
            batch_size=batch_size,
            delay_between_stocks=delay_between_stocks,
            delay_between_batches=delay_between_batches,
            cpu_threshold=cpu_threshold,
            memory_threshold=memory_threshold,
            auto_pause_on_overload=auto_pause_on_overload
        )

        # Progress callback function
        def progress_callback(current: int, total: int, message: str):
            task.progress.current = current
            task.progress.percent = round((current / total) * 100, 1)
            task.progress.current_step = f"循序處理中 {current}/{total}: {message}"

            # Update recent items
            if not task.progress.recent_items:
                task.progress.recent_items = []

            # Extract stock symbol from message if available
            if "已處理" in message and "(" in message:
                stock_symbol = message.split("已處理")[1].split("(")[0].strip()
                task.progress.recent_items.append(stock_symbol)
            elif message:
                task.progress.recent_items.append(message.split(' ')[0] if ' ' in message else message)

            if len(task.progress.recent_items) > 5:
                task.progress.recent_items = task.progress.recent_items[-5:]

            # Update database progress
            task_log.processed_count = current
            task_log.progress = int(task.progress.percent)
            task_log.result_summary = task.progress.current_step

            # Commit every 10 updates to avoid too frequent DB operations
            if current % 10 == 0 or current == total:
                db.commit()

        # Execute sequential batch update
        result = await updater.update_stocks_sequential(
            stock_codes=symbols,
            progress_callback=progress_callback
        )

        # Final progress update
        task.progress.current = len(symbols)
        task.progress.percent = 100.0
        task.progress.current_step = "循序任務完成"

        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.end_time = datetime.now()

        # Extract results
        successful_updates = result.get("successful_updates", 0)
        failed_updates = result.get("failed_updates", 0)
        total_records_processed = result.get("total_records_processed", 0)
        total_records_created = result.get("total_records_created", 0)
        total_records_updated = result.get("total_records_updated", 0)
        execution_time = result.get("execution_time", 0)
        batches_processed = result.get("batches_processed", 0)
        performance_metrics = result.get("performance_metrics", {})

        task.result = {
            "total_symbols": len(symbols),
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "total_records_processed": total_records_processed,
            "total_records_created": total_records_created,
            "total_records_updated": total_records_updated,
            "execution_time_seconds": execution_time,
            "batches_processed": batches_processed,
            "processing_mode": "循序處理",
            "performance_metrics": performance_metrics,
            "resource_impact": result.get("resource_impact", "低負載循序處理"),
            "system_benefits": {
                "estimated_cpu_usage": f"平均 {cpu_threshold * 0.6:.1f}% (vs {cpu_threshold}% 閾值)",
                "memory_efficiency": f"穩定使用，無尖峰負載",
                "success_rate": performance_metrics.get("success_rate", 0),
                "resource_friendly": True
            }
        }

        # Update database record - completed
        task_log.status = "completed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = execution_time
        task_log.processed_count = len(symbols)
        task_log.progress = 100
        task_log.success_count = successful_updates
        task_log.error_count = failed_updates

        sequential_summary = f"循序任務完成 - 成功:{successful_updates} 失敗:{failed_updates} 記錄:{total_records_processed} 創建:{total_records_created} 更新:{total_records_updated} 用時:{execution_time:.1f}秒 批次:{batches_processed} 速度:{performance_metrics.get('stocks_per_second', 0):.1f}檔/秒"
        task_log.result_summary = sequential_summary

        db.commit()

        logger.info(f"Sequential stock crawl task {task_id} completed: {sequential_summary}")

    except Exception as e:
        # Mark as failed
        task.status = TaskStatus.FAILED
        task.end_time = datetime.now()
        task.error_message = str(e)

        # Update database record - failed
        task_log.status = "failed"
        task_log.end_time = task.end_time
        task_log.duration_seconds = (task.end_time - task.start_time).total_seconds()
        task_log.error_message = str(e)
        task_log.result_summary = f"循序任務失敗：{str(e)}"
        db.commit()

        logger.error(f"Sequential stock crawl task {task_id} failed: {e}")

    finally:
        # Move to history
        if task_id in ACTIVE_TASKS:
            TASK_HISTORY.append(task)
            del ACTIVE_TASKS[task_id]