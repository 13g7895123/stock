#!/bin/bash

# Stock Analysis System - 启动脚本
# 使用 Docker Compose 启动所有服务

set -e

echo "🚀 启动股票分析系统..."
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在 docker 目录下运行此脚本"
    echo "   cd docker && ./start.sh"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "envs/.env" ]; then
    echo "❌ 错误: 找不到环境变量文件 envs/.env"
    echo "   请复制 envs/.env.example 到 envs/.env 并配置"
    exit 1
fi

# 停止旧容器
echo "📦 停止旧容器..."
docker compose --env-file envs/.env down 2>/dev/null || true

# 构建镜像
echo ""
echo "🔨 构建服务镜像..."
docker compose --env-file envs/.env build

# 启动服务
echo ""
echo "🎯 启动所有服务..."
docker compose --env-file envs/.env up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 显示服务状态
echo ""
echo "📊 服务状态:"
docker compose --env-file envs/.env ps

echo ""
echo "✅ 启动完成！"
echo ""
echo "📌 访问地址:"
echo "   - 前端应用: http://localhost:9727"
echo "   - 爬虫监控: http://localhost:9627"
echo "   - 数据库: localhost:9227"
echo ""
echo "💡 提示:"
echo "   - 查看日志: docker compose --env-file envs/.env logs -f [service]"
echo "   - 停止服务: docker compose --env-file envs/.env down"
echo "   - 重启服务: docker compose --env-file envs/.env restart [service]"
echo ""
