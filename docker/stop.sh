#!/bin/bash

# Stock Analysis System - 停止脚本

set -e

echo "🛑 停止股票分析系统..."
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在 docker 目录下运行此脚本"
    echo "   cd docker && ./stop.sh"
    exit 1
fi

# 停止所有服务
echo "📦 停止所有服务..."
docker compose --env-file envs/.env down

echo ""
echo "✅ 所有服务已停止"
echo ""
echo "💡 提示:"
echo "   - 重新启动: ./start.sh"
echo "   - 删除数据卷: docker compose --env-file envs/.env down -v"
echo ""
