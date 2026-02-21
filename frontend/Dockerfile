# 使用 Bun 官方镜像
FROM oven/bun:1 AS builder

WORKDIR /app

# 复制package.json
COPY package.json ./

# 安装依赖
RUN bun install

# 复制源代码
COPY . .

# 构建应用
RUN bun run build

# 生产环境
FROM oven/bun:1-alpine

WORKDIR /app

# 复制构建产物
COPY --from=builder /app/.output /app/.output

# 暴露端口
EXPOSE 3000

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

# 启动应用
CMD ["bun", "run", ".output/server/index.mjs"]
