# ==================== Stage 1: Builder ====================
FROM golang:1.21-alpine AS builder

# 安裝建構工具
RUN apk add --no-cache git make ca-certificates

# 設定工作目錄
WORKDIR /build

# 複製 go mod 檔案
COPY go.mod go.sum ./

# 下載依賴
RUN go mod download

# 複製原始碼
COPY . .

# 建構應用程式
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o crawler-service \
    ./cmd/crawler/main.go

# ==================== Stage 2: Runtime ====================
FROM alpine:latest

# 安裝必要的執行時依賴
RUN apk --no-cache add \
    ca-certificates \
    tzdata \
    && cp /usr/share/zoneinfo/Asia/Taipei /etc/localtime \
    && echo "Asia/Taipei" > /etc/timezone \
    && apk del tzdata

# 建立非 root 使用者
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# 設定工作目錄
WORKDIR /app

# 從 builder 複製執行檔
COPY --from=builder /build/crawler-service /app/crawler-service

# 複製配置檔案
COPY --from=builder /build/configs /app/configs

# 修改擁有者
RUN chown -R appuser:appuser /app

# 切換到非 root 使用者
USER appuser

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 啟動應用程式
ENTRYPOINT ["/app/crawler-service"]
