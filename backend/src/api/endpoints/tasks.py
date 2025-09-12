"""Manual task execution and tracking API endpoints."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.core.database import get_db
from src.services.daily_data_service import DailyDataService
from src.models.stock import Stock

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

async def run_stock_crawl_task(task_id: str, symbols: List[str], db: Session):
    """執行股票爬蟲任務的背景函數 - Background function for stock crawling task."""
    
    task = ACTIVE_TASKS.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    try:
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
                return
                
            try:
                # Update progress
                task.progress.current = i
                task.progress.percent = round((i / len(symbols)) * 100, 1)
                task.progress.current_step = f"正在處理第 {i+1} / {len(symbols)} 檔股票: {symbol}"
                
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
                    logger.info(f"Successfully processed {symbol}: {result.get('records_processed', 0)} records")
                else:
                    failed_updates += 1
                    logger.error(f"Failed to process {symbol}: {result.get('error', 'Unknown error')}")
                
                # Small delay to avoid overwhelming broker servers
                if i < len(symbols) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_updates += 1
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
        
        logger.info(f"Stock crawl task {task_id} completed: {successful_updates} success, {failed_updates} failed, {total_records_processed} records")
        
    except Exception as e:
        # Mark as failed
        task.status = TaskStatus.FAILED
        task.end_time = datetime.now()
        task.error_message = str(e)
        logger.error(f"Stock crawl task {task_id} failed: {e}")
        
    finally:
        # Move to history
        if task_id in ACTIVE_TASKS:
            TASK_HISTORY.append(task)
            del ACTIVE_TASKS[task_id]