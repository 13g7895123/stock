# Integration Tests Documentation

This directory contains comprehensive integration tests for the stock analysis application. These tests verify the complete data flow from API endpoints through the service layer to the PostgreSQL database.

## Test Categories

### 1. Database Integration Tests (`test_db_integration.py`)

Tests that verify real database operations using PostgreSQL:

- **Database Connection & Configuration**: Verifies connection to real PostgreSQL instance
- **CRUD Operations**: Tests create, read, update, delete operations on stock data  
- **Transaction Management**: Verifies proper commit/rollback behavior
- **Data Consistency**: Ensures data integrity across operations
- **Performance Testing**: Tests with larger datasets (100+ stocks)
- **Concurrent Access**: Tests multiple database sessions
- **Constraint Validation**: Tests database-level constraints and validation

**Key Test Methods:**
- `test_save_stocks_to_database_creates_records()` - Verifies stock creation
- `test_save_stocks_to_database_updates_existing_records()` - Tests updates  
- `test_get_stock_count_by_market_queries_database()` - Tests aggregations
- `test_deactivate_missing_stocks_updates_database()` - Tests soft deletes
- `test_sync_all_stocks_integration()` - Tests complete sync process
- `test_transaction_rollback_on_error()` - Tests error handling

### 2. End-to-End API Tests (`test_e2e_api.py`)

Tests that verify the complete API-to-database flow:

- **API Endpoint Testing**: Tests all stock sync API endpoints
- **Database Verification**: Verifies API operations persist to database
- **Data Flow Validation**: Tests complete request → service → database → response cycle
- **Error Handling**: Tests API error responses and database rollbacks
- **Performance Benchmarks**: Tests API response times
- **Concurrent Requests**: Tests multiple simultaneous API calls

**Key Test Methods:**
- `test_sync_stocks_api_creates_database_records()` - E2E sync test
- `test_get_stock_counts_api_reads_from_database()` - Read verification
- `test_data_persistence_across_api_calls()` - Persistence testing
- `test_sync_api_updates_existing_stocks()` - Update verification
- `test_api_error_handling_with_database_rollback()` - Error testing

## Prerequisites

### 1. Docker Services

Start the required Docker services:

```bash
# From project root directory
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

**Required Services:**
- **PostgreSQL**: `localhost:5432` 
  - Database: `stock_analysis`
  - User: `stock_user`
  - Password: `password`
- **FastAPI Backend**: `localhost:8000`
  - Health check: `GET /health`
- **Redis**: `localhost:6379` (for caching/sessions)

### 2. Python Dependencies

Install test dependencies:

```bash
# From backend directory
pip install -r requirements.txt
pip install pytest httpx psycopg2-binary asyncpg
```

### 3. Database Schema

Ensure database tables are created:

```bash
# From backend directory  
alembic upgrade head
```

## Running the Tests

### Option 1: Using the Test Runner Script (Recommended)

```bash
# Run all integration tests
python tests/run_integration_tests.py

# Run only database tests
python tests/run_integration_tests.py --db-only

# Run only API tests  
python tests/run_integration_tests.py --api-only

# Verbose output
python tests/run_integration_tests.py --verbose

# Skip service health checks (if services already verified)
python tests/run_integration_tests.py --skip-setup
```

### Option 2: Using pytest Directly

```bash
# From backend directory

# Run all integration tests
pytest tests/test_db_integration.py tests/test_e2e_api.py -v

# Run only database integration tests
pytest tests/test_db_integration.py -v

# Run only API integration tests
pytest tests/test_e2e_api.py -v

# Run with specific markers
pytest -m "integration" -v
pytest -m "postgres" -v  
pytest -m "api" -v

# Skip slow tests
pytest -m "not slow" tests/test_db_integration.py -v
```

### Option 3: Individual Test Classes

```bash
# Run specific test class
pytest tests/test_db_integration.py::TestDatabaseIntegration -v

# Run specific test method  
pytest tests/test_db_integration.py::TestDatabaseIntegration::test_save_stocks_to_database_creates_records -v
```

## Test Configuration

### Environment Variables

```bash
# Optional: Override default configuration
export TEST_DATABASE_URL="postgresql://stock_user:password@localhost:5432/stock_analysis"
export TEST_API_BASE_URL="http://localhost:8000"

# Skip integration tests (useful in CI without Docker)
export SKIP_INTEGRATION_TESTS=1
```

### pytest.ini Configuration

Add to `pytest.ini`:

```ini
[tool:pytest]
markers = 
    integration: marks tests as integration tests
    postgres: marks tests that require PostgreSQL
    api: marks tests that require API service  
    slow: marks tests as slow running
    docker: marks tests that require Docker services
    
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Test Data Management

### Test Data Patterns

Tests use specific symbol patterns to avoid conflicts:

- **Database Integration Tests**: Symbols starting with `8` (e.g., `8001`, `8002`)
- **API Integration Tests**: Symbols starting with `9` (e.g., `9001`, `9002`)  
- **Performance Tests**: Symbols in range `9100-9199`
- **Standard Test Data**: Known symbols `1101`, `2330`, `3008`, `4938`

### Data Cleanup

Tests automatically clean up their data:

- **Before Each Test**: Clean test symbols from database
- **After Each Test**: Remove any created test data
- **Test Runner**: Comprehensive cleanup before/after test suite

### Manual Cleanup

If needed, manually clean test data:

```sql
-- Connect to PostgreSQL
DELETE FROM stocks WHERE symbol LIKE '8%' OR symbol LIKE '9%';
DELETE FROM stocks WHERE symbol IN ('1101', '2330', '3008', '4938');
```

## Troubleshooting

### Common Issues

1. **"PostgreSQL not available"**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check connection
   psql -h localhost -p 5432 -U stock_user -d stock_analysis
   ```

2. **"API not available"** 
   ```bash
   # Check if API is running
   curl http://localhost:8000/health
   
   # Check Docker logs
   docker-compose logs backend
   ```

3. **"Tests timing out"**
   ```bash
   # Increase timeout in test configuration
   # Or run with --skip-setup if services are verified
   python tests/run_integration_tests.py --skip-setup
   ```

4. **"Database connection errors"**
   ```bash
   # Reset database connection
   docker-compose restart postgres
   
   # Wait for health check
   docker-compose ps
   ```

### Debug Mode

Run tests with maximum verbosity:

```bash
# Full debug output
pytest tests/test_db_integration.py -v -s --tb=long

# With test runner
python tests/run_integration_tests.py --verbose
```

### Check Service Health

Before running tests, verify services:

```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U stock_user

# API Health
curl -f http://localhost:8000/health

# All services  
docker-compose ps
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: stock_analysis
          POSTGRES_USER: stock_user
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install pytest httpx psycopg2-binary
    
    - name: Run integration tests
      run: |
        cd backend
        python tests/run_integration_tests.py --skip-setup
```

## Test Coverage

These integration tests provide coverage for:

- ✅ **Database Operations**: All CRUD operations with real PostgreSQL
- ✅ **API Endpoints**: All stock sync endpoints with database verification
- ✅ **Data Integrity**: Transaction consistency and rollback behavior  
- ✅ **Error Handling**: Database errors, API errors, external service failures
- ✅ **Performance**: Response times and throughput with realistic data volumes
- ✅ **Concurrency**: Multiple simultaneous operations
- ✅ **Data Validation**: Business rules and database constraints

## Metrics and Reporting

### Test Execution Metrics

- **Database Tests**: ~15 tests, ~10-30 seconds execution
- **API Tests**: ~10 tests, ~20-60 seconds execution  
- **Total Coverage**: 25+ integration test scenarios

### Performance Benchmarks

- API responses: < 2 seconds for normal operations
- Database operations: < 5 seconds for 100+ stock batch
- Sync operations: < 30 seconds for complete stock list

## Best Practices

1. **Test Isolation**: Each test cleans its own data
2. **Real Services**: Tests run against actual PostgreSQL and API
3. **Data Verification**: All operations verified in database
4. **Error Testing**: Comprehensive error scenario coverage
5. **Performance Aware**: Tests include timing assertions
6. **CI Friendly**: Can be run in automated environments

For more details, see the individual test files and their comprehensive docstrings.