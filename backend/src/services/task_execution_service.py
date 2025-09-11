"""Task execution logging service."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models.stock import TaskExecutionLog

logger = logging.getLogger(__name__)


class TaskExecutionService:
    """Service for managing task execution logs."""
    
    def __init__(self, db_session: Session):
        """Initialize the task execution service."""
        self.db_session = db_session
    
    def start_task(
        self,
        task_name: str,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        total_count: int = 0,
        created_by: str = "system"
    ) -> int:
        """開始一個新任務並返回任務ID."""
        try:
            task_log = TaskExecutionLog(
                task_name=task_name,
                task_type=task_type,
                parameters=json.dumps(parameters) if parameters else None,
                status="running",
                start_time=datetime.now(timezone.utc),
                total_count=total_count,
                created_by=created_by
            )
            
            self.db_session.add(task_log)
            self.db_session.commit()
            self.db_session.refresh(task_log)
            
            logger.info(f"Started task: {task_name} (ID: {task_log.id})")
            return task_log.id
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error starting task {task_name}: {e}")
            raise
    
    def update_progress(
        self,
        task_id: int,
        progress: Optional[int] = None,
        processed_count: Optional[int] = None,
        success_count: Optional[int] = None,
        error_count: Optional[int] = None,
        result_summary: Optional[str] = None
    ) -> bool:
        """更新任務執行進度."""
        try:
            task_log = self.db_session.query(TaskExecutionLog).filter(
                TaskExecutionLog.id == task_id
            ).first()
            
            if not task_log:
                logger.warning(f"Task ID {task_id} not found")
                return False
            
            if progress is not None:
                task_log.progress = max(0, min(100, progress))
            
            if processed_count is not None:
                task_log.processed_count = processed_count
            
            if success_count is not None:
                task_log.success_count = success_count
            
            if error_count is not None:
                task_log.error_count = error_count
            
            if result_summary is not None:
                task_log.result_summary = result_summary
            
            # 自動計算進度（如果有總數和處理數）
            if task_log.total_count > 0 and processed_count is not None:
                calculated_progress = int((processed_count / task_log.total_count) * 100)
                task_log.progress = calculated_progress
            
            self.db_session.commit()
            logger.debug(f"Updated task {task_id} progress: {task_log.progress}%")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error updating task progress {task_id}: {e}")
            return False
    
    def complete_task(
        self,
        task_id: int,
        status: str = "completed",
        result_summary: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """完成任務並記錄結果."""
        try:
            task_log = self.db_session.query(TaskExecutionLog).filter(
                TaskExecutionLog.id == task_id
            ).first()
            
            if not task_log:
                logger.warning(f"Task ID {task_id} not found")
                return False
            
            end_time = datetime.now(timezone.utc)
            task_log.end_time = end_time
            task_log.status = status
            
            if result_summary is not None:
                task_log.result_summary = result_summary
            
            if error_message is not None:
                task_log.error_message = error_message
            
            # 計算執行時間
            if task_log.start_time:
                duration = (end_time - task_log.start_time).total_seconds()
                task_log.duration_seconds = duration
            
            # 如果狀態是完成，設置進度為100%
            if status == "completed":
                task_log.progress = 100
            
            self.db_session.commit()
            
            logger.info(
                f"Completed task {task_id} ({task_log.task_name}) - "
                f"Status: {status}, Duration: {task_log.duration_seconds:.2f}s"
            )
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error completing task {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """獲取任務狀態."""
        try:
            task_log = self.db_session.query(TaskExecutionLog).filter(
                TaskExecutionLog.id == task_id
            ).first()
            
            if not task_log:
                return None
            
            return {
                "id": task_log.id,
                "task_name": task_log.task_name,
                "task_type": task_log.task_type,
                "status": task_log.status,
                "progress": task_log.progress,
                "processed_count": task_log.processed_count,
                "total_count": task_log.total_count,
                "success_count": task_log.success_count,
                "error_count": task_log.error_count,
                "start_time": task_log.start_time.isoformat() if task_log.start_time else None,
                "end_time": task_log.end_time.isoformat() if task_log.end_time else None,
                "duration_seconds": task_log.duration_seconds,
                "result_summary": task_log.result_summary,
                "error_message": task_log.error_message,
                "created_by": task_log.created_by
            }
            
        except Exception as e:
            logger.error(f"Error getting task status {task_id}: {e}")
            return None
    
    def get_recent_tasks(
        self,
        limit: int = 50,
        task_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """獲取最近的任務列表."""
        try:
            query = self.db_session.query(TaskExecutionLog)
            
            if task_type:
                query = query.filter(TaskExecutionLog.task_type == task_type)
            
            if status:
                query = query.filter(TaskExecutionLog.status == status)
            
            tasks = query.order_by(desc(TaskExecutionLog.start_time)).limit(limit).all()
            
            result = []
            for task in tasks:
                result.append({
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "status": task.status,
                    "progress": task.progress,
                    "processed_count": task.processed_count,
                    "total_count": task.total_count,
                    "success_count": task.success_count,
                    "error_count": task.error_count,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "duration_seconds": task.duration_seconds,
                    "result_summary": task.result_summary,
                    "error_message": task.error_message,
                    "created_by": task.created_by
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent tasks: {e}")
            return []
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """獲取正在運行的任務."""
        return self.get_recent_tasks(limit=20, status="running")
    
    def cancel_task(self, task_id: int, reason: str = "Cancelled by user") -> bool:
        """取消任務."""
        return self.complete_task(
            task_id=task_id,
            status="cancelled",
            error_message=reason
        )