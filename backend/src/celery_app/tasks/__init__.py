"""Celery tasks package."""

# 匯入所有任務模組以確保任務被註冊
from . import data_collection
from . import analysis

__all__ = ['data_collection', 'analysis']