# 🐳 Docker 启动指南

## ✅ 已成功启动！

监控面板已通过 Docker 成功部署并运行。

---

## 📊 访问监控面板

### **监控面板（Dashboard）**
```
http://localhost:9627
```

### **API 端点**
```bash
# 健康检查
http://localhost:9627/health

# 股票统计 API
http://localhost:9627/api/v1/stats/stocks-summary

# 爬取单一股票
http://localhost:9627/api/v1/stocks/2330/daily
```

---

## 🚀 Docker 服务管理

### **查看运行状态**
```bash
cd /home/jarvis/project/idea/stock/crawler-service
docker compose ps
```

### **查看日志**
```bash
# 查看所有服务日志
docker compose logs -f

# 只查看 crawler 服务日志
docker compose logs -f crawler-service

# 只查看数据库日志
docker compose logs -f postgres
```

### **停止服务**
```bash
docker compose down
```

### **重启服务**
```bash
docker compose restart
```

### **完全清理（包括数据）**
```bash
docker compose down -v
```

---

## 📦 服务信息

### **运行中的容器**
- `stock_crawler_dashboard` - Go 爬虫服务 + 监控面板
- `crawler_postgres` - PostgreSQL 数据库

### **端口映射**
- **9627** → 监控面板 & API 服务
- **9221** → PostgreSQL 数据库

### **数据库连接信息**
```
Host: localhost
Port: 9221
Database: stock_analysis
User: stock_user
Password: password
```

---

## 🧪 测试功能

### **1. 测试健康检查**
```bash
curl http://localhost:9627/health
```

### **2. 查看统计数据**
```bash
curl http://localhost:9627/api/v1/stats/stocks-summary
```

### **3. 爬取股票数据（批次）**
```bash
curl -X POST http://localhost:9627/api/v1/stocks/batch-update \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454"]}'
```

### **4. 查看已爬取的数据**
```bash
# 直接访问监控面板
open http://localhost:9627
# 或在 WSL 中
explorer.exe http://localhost:9627
```

---

## 🔧 故障排除

### **问题 1：无法访问 http://localhost:9627**

**检查容器状态：**
```bash
docker ps | grep crawler
```

**如果容器未运行，重新启动：**
```bash
cd /home/jarvis/project/idea/stock/crawler-service
docker compose up -d
```

### **问题 2：页面显示"载入失败"**

**检查数据库连接：**
```bash
docker exec -it crawler_postgres psql -U stock_user -d stock_analysis -c "SELECT COUNT(*) FROM stocks;"
```

**如果表不存在，重新创建：**
```bash
docker exec -i crawler_postgres psql -U stock_user -d stock_analysis << 'EOF'
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) UNIQUE NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    market VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_daily_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    volume BIGINT,
    turnover NUMERIC(15, 2),
    data_source VARCHAR(50),
    data_quality VARCHAR(20),
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);
EOF
```

### **问题 3：端口冲突**

**如果 9627 端口被占用，修改端口：**
```bash
# 编辑 docker-compose.yml
nano docker-compose.yml

# 修改这一行（例如改为 9628）
# ports:
#   - "9628:8080"

# 重新启动
docker compose down
docker compose up -d
```

### **问题 4：查看详细错误日志**

```bash
# 查看 crawler 服务日志
docker logs stock_crawler_dashboard --tail 100

# 实时追踪日志
docker logs -f stock_crawler_dashboard
```

---

## 📝 数据库操作

### **连接数据库**
```bash
docker exec -it crawler_postgres psql -U stock_user -d stock_analysis
```

### **查询股票列表**
```sql
SELECT * FROM stocks;
```

### **查询资料笔数**
```sql
SELECT 
    stock_code, 
    COUNT(*) as count,
    MIN(trade_date) as first_date,
    MAX(trade_date) as latest_date
FROM stock_daily_data
GROUP BY stock_code;
```

### **插入测试股票**
```sql
INSERT INTO stocks (stock_code, stock_name, market, is_active) 
VALUES 
    ('2882', '国泰金', 'TSE', true),
    ('2412', '中华电', 'TSE', true)
ON CONFLICT (stock_code) DO NOTHING;
```

---

## 🔄 更新部署

### **如果修改了代码，重新构建并部署：**

```bash
cd /home/jarvis/project/idea/stock/crawler-service

# 1. 重新构建镜像
docker build -t stock-crawler-service:latest -f deployments/Dockerfile .

# 2. 停止并移除旧容器
docker compose down

# 3. 启动新容器
docker compose up -d

# 4. 查看日志确认启动成功
docker compose logs -f crawler-service
```

---

## 📊 监控面板功能

访问 http://localhost:9627 后，你可以：

1. ✅ **查看统计卡片**
   - 总股票数
   - 总资料笔数
   - 平均笔数
   - 服务状态

2. ✅ **浏览股票清单表格**
   - 所有股票及其资料笔数
   - 起始日期、最新日期
   - 资料来源

3. ✅ **互动功能**
   - 🔍 搜寻股票
   - ⬆️⬇️ 排序栏位
   - 🔄 手动刷新
   - 📥 汇出 CSV

4. ✅ **自动更新**
   - 每 30 秒自动重新整理资料

---

## 🎯 快速开始示例

### **完整工作流程：**

```bash
# 1. 启动服务（已完成）
cd /home/jarvis/project/idea/stock/crawler-service
docker compose up -d

# 2. 确认服务运行
docker compose ps

# 3. 爬取一些股票数据
curl -X POST http://localhost:9627/api/v1/stocks/batch-update \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["2330", "2317", "2454", "2882", "2412"]}'

# 4. 等待几分钟后，访问监控面板
# 浏览器打开: http://localhost:9627

# 5. 查看日志（可选）
docker compose logs -f crawler-service
```

---

## 🌐 在浏览器中打开

### **Windows (WSL):**
```bash
explorer.exe http://localhost:9627
```

### **Linux (有桌面环境):**
```bash
xdg-open http://localhost:9627
```

### **macOS:**
```bash
open http://localhost:9627
```

---

## 📂 项目文件

```
crawler-service/
├── docker-compose.yml          # Docker Compose 配置
├── deployments/
│   └── Dockerfile             # Docker 镜像构建文件
├── web/
│   └── index.html            # 监控面板 HTML
├── configs/
│   └── config.yaml           # 服务配置
└── DOCKER_GUIDE.md           # 本文件
```

---

## ✅ 当前状态

- ✅ Docker 镜像已构建
- ✅ 服务已启动运行
- ✅ 数据库已初始化
- ✅ 监控面板可访问
- ✅ API 端点正常工作

**立即访问：** http://localhost:9627

---

**需要帮助？** 查看日志或检查上述故障排除章节。

**祝使用愉快！** 🎉
