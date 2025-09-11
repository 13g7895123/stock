"""Task execution management API endpoints."""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.task_execution_service import TaskExecutionService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_task_execution_service(db: Session = Depends(get_db)) -> TaskExecutionService:
    """Get task execution service instance."""
    return TaskExecutionService(db)


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: int,
    service: TaskExecutionService = Depends(get_task_execution_service)
):
    """
    獲取特定任務的狀態
    
    - **task_id**: 任務ID
    """
    try:
        task_status = service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "status": "success",
            "task": task_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recent", response_model=Dict[str, Any])
async def get_recent_tasks(
    limit: int = Query(50, ge=1, le=100),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: TaskExecutionService = Depends(get_task_execution_service)
):
    """
    獲取最近的任務列表
    
    - **limit**: 返回數量限制 (1-100)
    - **task_type**: 任務類型篩選
    - **status**: 狀態篩選 (running, completed, failed, cancelled)
    """
    try:
        tasks = service.get_recent_tasks(
            limit=limit,
            task_type=task_type,
            status=status
        )
        
        return {
            "status": "success",
            "tasks": tasks,
            "total": len(tasks),
            "filters": {
                "task_type": task_type,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recent tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/running", response_model=Dict[str, Any])
async def get_running_tasks(
    service: TaskExecutionService = Depends(get_task_execution_service)
):
    """
    獲取正在運行的任務列表
    """
    try:
        running_tasks = service.get_running_tasks()
        
        return {
            "status": "success",
            "running_tasks": running_tasks,
            "count": len(running_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error getting running tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cancel/{task_id}", response_model=Dict[str, Any])
async def cancel_task(
    task_id: int,
    reason: str = Query("Cancelled by user request"),
    service: TaskExecutionService = Depends(get_task_execution_service)
):
    """
    取消執行中的任務
    
    - **task_id**: 任務ID
    - **reason**: 取消原因
    """
    try:
        success = service.cancel_task(task_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")
        
        return {
            "status": "success",
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_task_statistics(
    service: TaskExecutionService = Depends(get_task_execution_service)
):
    """
    獲取任務執行統計
    """
    try:
        # 獲取最近100個任務進行統計
        recent_tasks = service.get_recent_tasks(limit=100)
        
        if not recent_tasks:
            return {
                "status": "success",
                "statistics": {
                    "total_tasks": 0,
                    "running_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "cancelled_count": 0,
                    "success_rate": 0.0,
                    "average_duration": 0.0
                }
            }
        
        # 統計各種狀態的任務數量
        status_counts = {}
        total_duration = 0
        duration_count = 0
        
        for task in recent_tasks:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if task["duration_seconds"]:
                total_duration += task["duration_seconds"]
                duration_count += 1
        
        # 計算成功率
        completed = status_counts.get("completed", 0)
        failed = status_counts.get("failed", 0)
        cancelled = status_counts.get("cancelled", 0)
        total_finished = completed + failed + cancelled
        success_rate = (completed / total_finished * 100) if total_finished > 0 else 0
        
        # 計算平均執行時間
        average_duration = total_duration / duration_count if duration_count > 0 else 0
        
        statistics = {
            "total_tasks": len(recent_tasks),
            "running_count": status_counts.get("running", 0),
            "completed_count": completed,
            "failed_count": failed,
            "cancelled_count": cancelled,
            "success_rate": round(success_rate, 2),
            "average_duration": round(average_duration, 2)
        }
        
        return {
            "status": "success",
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")