.PHONY: help build run test test-unit test-integration test-coverage clean lint fmt docker-build docker-run

# 變數
BINARY_NAME=crawler-service
DOCKER_IMAGE=stock-crawler
VERSION?=v1.0.0

help: ## 顯示幫助資訊
	@echo "可用的命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## 建構應用程式
	@echo "Building $(BINARY_NAME)..."
	go build -o bin/$(BINARY_NAME) ./cmd/crawler/main.go

build-linux: ## 建構 Linux 版本
	@echo "Building $(BINARY_NAME) for Linux..."
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o bin/$(BINARY_NAME)-linux ./cmd/crawler/main.go

run: ## 執行應用程式
	@echo "Running $(BINARY_NAME)..."
	go run ./cmd/crawler/main.go

test: test-unit test-integration ## 執行所有測試

test-unit: ## 執行單元測試
	@echo "Running unit tests..."
	go test -v -race -cover ./tests/unit/...

test-integration: ## 執行整合測試
	@echo "Running integration tests..."
	go test -v -tags=integration ./tests/integration/...

test-coverage: ## 產生測試覆蓋率報告
	@echo "Generating coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

test-bench: ## 執行效能測試
	@echo "Running benchmarks..."
	go test -bench=. -benchmem ./...

lint: ## 執行程式碼檢查
	@echo "Running linters..."
	golangci-lint run ./...

fmt: ## 格式化程式碼
	@echo "Formatting code..."
	go fmt ./...
	goimports -w .

vet: ## 執行 go vet 檢查
	@echo "Running go vet..."
	go vet ./...

clean: ## 清理建構檔案
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out coverage.html

deps: ## 下載依賴
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy

docker-build: ## 建構 Docker 映像
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(VERSION) -f deployments/Dockerfile .
	docker tag $(DOCKER_IMAGE):$(VERSION) $(DOCKER_IMAGE):latest

docker-run: ## 執行 Docker 容器
	@echo "Running Docker container..."
	docker run -d \
		--name $(BINARY_NAME) \
		-p 8080:8080 \
		-e DATABASE_URL="postgresql://stock_user:password@host.docker.internal:9221/stock_analysis" \
		$(DOCKER_IMAGE):latest

docker-stop: ## 停止 Docker 容器
	@echo "Stopping Docker container..."
	docker stop $(BINARY_NAME)
	docker rm $(BINARY_NAME)

docker-compose-up: ## 啟動所有服務
	@echo "Starting services with docker-compose..."
	docker-compose -f deployments/docker-compose.yml up -d

docker-compose-down: ## 停止所有服務
	@echo "Stopping services..."
	docker-compose -f deployments/docker-compose.yml down

logs: ## 查看日誌
	docker logs -f $(BINARY_NAME)

install-tools: ## 安裝開發工具
	@echo "Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install golang.org/x/tools/cmd/goimports@latest

.DEFAULT_GOAL := help
