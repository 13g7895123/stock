"""Router factory for organizing API routes.

集中管理所有路由的註冊，使 main.py 更加簡潔。
"""
from fastapi import FastAPI

from src.api.endpoints import (
    health,
    stocks,
    stock_sync,
    data,
    tasks,
    task_execution,
    moving_averages,
    stock_selection,
    twse,
    trading_days,
    capital_stock,
    institutional_trading,
)


# Router configuration
ROUTER_CONFIGS = [
    {
        "router": health.router,
        "prefix": "/api/v1/health",
        "tags": ["Health Check"],
    },
    {
        "router": stocks.router,
        "prefix": "/api/v1/stocks",
        "tags": ["Stocks"],
    },
    {
        "router": stock_sync.router,
        "prefix": "/api/v1/sync",
        "tags": ["Stock Synchronization"],
    },
    {
        "router": data.router,
        "prefix": "/api/v1/data",
        "tags": ["Data Management"],
    },
    {
        "router": tasks.router,
        "prefix": "/api/v1/tasks",
        "tags": ["Task Management"],
    },
    {
        "router": task_execution.router,
        "prefix": "/api/v1/task-execution",
        "tags": ["Task Execution Logs"],
    },
    {
        "router": moving_averages.router,
        "prefix": "/api/v1/moving-averages",
        "tags": ["Moving Averages"],
    },
    {
        "router": stock_selection.router,
        "prefix": "/api/v1/stock-selection",
        "tags": ["Stock Selection"],
    },
    {
        "router": twse.router,
        "prefix": "/api/v1/twse",
        "tags": ["TWSE Official API"],
    },
    {
        "router": trading_days.router,
        "prefix": "/api/v1/trading-days",
        "tags": ["Trading Days Analysis"],
    },
    {
        "router": capital_stock.router,
        "prefix": "/api/v1/capital-stock",
        "tags": ["Capital Stock Data"],
    },
    {
        "router": institutional_trading.router,
        "prefix": "/api/v1/institutional-trading",
        "tags": ["Institutional Trading Data"],
    },
]


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    for config in ROUTER_CONFIGS:
        app.include_router(
            config["router"],
            prefix=config["prefix"],
            tags=config["tags"],
        )
