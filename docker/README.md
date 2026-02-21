# Docker 目录说明

此目录包含所有 Docker 相关配置文件，使用标准的 Docker 方式管理整个项目。

## 目录结构

```
docker/
├── envs/               # 环境变量配置
│   └── .env           # 主环境变量文件
├── docker-compose.yml  # Docker Compose 配置
└── README.md          # 本文件
```

## 使用方法

### 启动所有服务

```bash
cd docker
docker compose --env-file envs/.env up -d
```

### 停止所有服务

```bash
cd docker
docker compose down
```

### 查看服务状态

```bash
cd docker
docker compose ps
```

### 查看服务日志

```bash
cd docker
docker compose logs -f [service_name]
```

### 重新构建服务

```bash
cd docker
docker compose build --no-cache
docker compose up -d
```

## 服务端口

| 服务 | 容器名称 | 端口 | 说明 |
|------|---------|------|------|
| PostgreSQL | stock-postgres | 9227 | 数据库服务 |
| Redis | stock-redis | 9327 | 缓存服务 |
| Go Crawler | stock-crawler | 9627 | 爬虫服务 + 监控面板 |
| Nuxt Frontend | stock-frontend | 9727 | 前端应用 |

## 环境变量配置

所有环境变量都在 `envs/.env` 文件中配置，包括：

- **容器名称**：所有容器名称通过环境变量控制
- **网络配置**：网络名称可自定义
- **卷配置**：数据卷名称可自定义
- **端口映射**：所有对外端口可配置
- **应用配置**：数据库、Redis、日志等配置

## Docker 标准实践

本配置遵循 Docker 官方最佳实践：

1. ✅ 所有容器名称通过环境变量控制
2. ✅ 使用命名卷管理持久化数据
3. ✅ 使用自定义网络隔离服务
4. ✅ 健康检查确保服务可用性
5. ✅ 使用 `depends_on` 管理服务依赖
6. ✅ 环境变量集中管理
7. ✅ 多阶段构建优化镜像大小

## 注意事项

1. 首次启动前请检查 `envs/.env` 文件中的配置
2. 确保端口未被占用
3. 生产环境请修改默认密码和密钥
4. 数据库数据持久化在 Docker 卷中
