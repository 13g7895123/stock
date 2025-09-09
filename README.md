# Stock Analysis System

A comprehensive stock analysis system built with FastAPI, providing real-time market data collection, technical analysis, and trading signals.

## Architecture Overview

```
stock-analysis-system/
├── backend/                    # Python FastAPI Backend
│   ├── src/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core configurations
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic services
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── utils/             # Utility functions
│   │   ├── celery_app/        # Celery tasks and configuration
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Test suites
│   ├── alembic/               # Database migrations
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Frontend application (admin panel)
├── docs/                      # Documentation
├── docker-compose.yml         # Docker services configuration
├── .env.example              # Environment variables template
└── .gitignore                # Git ignore patterns
```

## Features

### Core Features
- **Real-time Market Data**: Collect and store stock market data from multiple sources
- **Technical Analysis**: Calculate various technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- **Trading Signals**: Generate automated buy/sell/hold signals based on technical analysis
- **Background Tasks**: Asynchronous data processing with Celery
- **RESTful API**: Well-documented REST API for all functionality
- **Database Management**: PostgreSQL with SQLAlchemy ORM and Alembic migrations

### Technical Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- **Task Queue**: Celery with Redis broker
- **Technical Analysis**: pandas, TA-Lib, numpy
- **API Documentation**: Swagger/OpenAPI auto-generated docs
- **Containerization**: Docker and Docker Compose
- **Code Quality**: Black, isort, flake8, mypy, pre-commit hooks

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-analysis-system
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration values.

3. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

### Database Setup

1. **Start PostgreSQL and Redis** (if not using Docker)
   ```bash
   # Using Docker
   docker-compose up -d postgres redis
   ```

2. **Run database migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

### Running the Application

#### Option 1: Local Development
```bash
# Terminal 1: Start the FastAPI server
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A src.celery_app.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat scheduler
celery -A src.celery_app.celery_app beat --loglevel=info

# Terminal 4: Start Celery flower (monitoring)
celery -A src.celery_app.celery_app flower --port=5555
```

#### Option 2: Docker Compose
```bash
docker-compose up -d
```

### API Access

- **API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Celery Monitoring**: http://localhost:5555

## API Endpoints

### Health Checks
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system health
- `GET /api/v1/health/readiness` - Kubernetes readiness probe
- `GET /api/v1/health/liveness` - Kubernetes liveness probe

### Stock Data
- `GET /api/v1/stocks/symbols` - List available stock symbols
- `GET /api/v1/stocks/{symbol}/current` - Current stock price
- `GET /api/v1/stocks/{symbol}/historical` - Historical price data
- `POST /api/v1/stocks/{symbol}/update` - Trigger data update
- `POST /api/v1/stocks/update-all` - Update all symbols

### Technical Analysis
- `GET /api/v1/stocks/{symbol}/analysis` - Technical analysis results
- `POST /api/v1/stocks/{symbol}/analyze` - Trigger analysis
- `GET /api/v1/stocks/{symbol}/signals` - Trading signals
- `POST /api/v1/stocks/signals/generate` - Generate signals

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for quality checks

Run quality checks:
```bash
cd backend
make format      # Format code
make lint        # Run linting
make type-check  # Run type checking
make test        # Run tests
make test-cov    # Run tests with coverage
```

### Testing

Run tests:
```bash
cd backend
pytest -v                    # Run all tests
pytest -v --cov=src         # Run with coverage
pytest -v tests/test_health.py  # Run specific test file
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `DEFAULT_STOCK_SYMBOLS`: Comma-separated list of default symbols

### Technical Analysis Settings

- `ANALYSIS_LOOKBACK_DAYS`: Days of historical data for analysis (default: 252)
- `DATA_UPDATE_INTERVAL_MINUTES`: How often to update data (default: 60)

## Monitoring and Logging

- **Application Logs**: Structured JSON logging to files and stdout
- **Celery Monitoring**: Flower web interface at http://localhost:5555
- **Health Checks**: Multiple health check endpoints for monitoring
- **Metrics**: Built-in application metrics (when enabled)

## Production Deployment

### Docker Production

1. **Update environment variables** for production
2. **Use production Docker Compose profile**:
   ```bash
   docker-compose --profile production up -d
   ```

### Key Production Considerations

- Set `DEBUG=false`
- Use strong `SECRET_KEY`
- Configure proper CORS origins
- Set up SSL certificates
- Use environment-specific database credentials
- Configure log rotation
- Set up monitoring and alerting
- Use Redis password authentication
- Configure rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following code quality standards
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license here]

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the health check endpoints
- Check application logs for errors
- Monitor Celery tasks in Flower

## Roadmap

- [ ] Additional data sources integration
- [ ] More technical indicators
- [ ] Portfolio management features
- [ ] Machine learning models
- [ ] WebSocket real-time updates
- [ ] Advanced alert system