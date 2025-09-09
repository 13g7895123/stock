.PHONY: help install install-dev format lint type-check test test-cov clean run-dev run-prod migrate upgrade downgrade celery-worker celery-beat celery-flower

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pre-commit install

format: ## Format code with black and isort
	black src tests
	isort src tests

lint: ## Run linting checks
	flake8 src tests
	black --check src tests
	isort --check-only src tests

type-check: ## Run type checking with mypy
	mypy src

test: ## Run tests
	pytest -v

test-cov: ## Run tests with coverage
	pytest -v --cov=src --cov-report=term-missing --cov-report=html

clean: ## Clean up build artifacts and cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

run-dev: ## Run development server
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

migrate: ## Generate new migration
	alembic revision --autogenerate -m "$(MSG)"

upgrade: ## Apply database migrations
	alembic upgrade head

downgrade: ## Rollback database migrations
	alembic downgrade -1

celery-worker: ## Start Celery worker
	celery -A src.celery_app.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	celery -A src.celery_app.celery_app beat --loglevel=info

celery-flower: ## Start Celery flower monitoring
	celery -A src.celery_app.celery_app flower