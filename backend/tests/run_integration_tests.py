#!/usr/bin/env python3
"""
Integration Test Runner Script

This script runs comprehensive database and API integration tests against
the Docker services. It ensures proper test environment setup and cleanup.

Usage:
    python run_integration_tests.py [options]
    
Options:
    --db-only       Run only database integration tests
    --api-only      Run only API integration tests  
    --skip-setup    Skip Docker service health checks
    --verbose       Verbose output
"""
import argparse
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict
import httpx
import psycopg2
from sqlalchemy import create_engine, text


# Configuration
POSTGRES_URL = "postgresql://stock_user:password@localhost:5432/stock_analysis"
API_BASE_URL = "http://localhost:8000"
DOCKER_COMPOSE_FILE = "../docker-compose.yml"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Manages integration test execution and environment setup."""
    
    def __init__(self, args):
        self.args = args
        self.verbose = args.verbose
        
    def check_docker_services(self, timeout: int = 60) -> bool:
        """Check if Docker services are running and healthy."""
        logger.info("Checking Docker services...")
        
        services_status = {
            "postgres": False,
            "api": False
        }
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check PostgreSQL
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="stock_analysis",
                    user="stock_user", 
                    password="password"
                )
                conn.close()
                services_status["postgres"] = True
                logger.info("✓ PostgreSQL is ready")
            except Exception as e:
                if self.verbose:
                    logger.debug(f"PostgreSQL not ready: {e}")
                
            # Check API
            try:
                response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
                if response.status_code == 200:
                    services_status["api"] = True
                    logger.info("✓ API service is ready")
            except Exception as e:
                if self.verbose:
                    logger.debug(f"API not ready: {e}")
            
            if all(services_status.values()):
                logger.info("All services are ready!")
                return True
                
            time.sleep(2)
        
        # Report which services are not ready
        failed_services = [name for name, status in services_status.items() if not status]
        logger.error(f"Services not ready after {timeout}s: {failed_services}")
        return False

    def setup_test_environment(self) -> bool:
        """Setup test environment and ensure clean state."""
        logger.info("Setting up test environment...")
        
        try:
            # Clean test data from database
            engine = create_engine(POSTGRES_URL)
            with engine.connect() as conn:
                # Remove test stocks (symbols starting with test patterns)
                test_patterns = ['9%', '8%', '7%']
                for pattern in test_patterns:
                    conn.execute(
                        text("DELETE FROM stocks WHERE symbol LIKE :pattern"),
                        {"pattern": pattern}
                    )
                
                # Remove specific test symbols
                test_symbols = ['1101', '2330', '3008', '4938', '6505']
                for symbol in test_symbols:
                    conn.execute(
                        text("DELETE FROM stocks WHERE symbol = :symbol"),
                        {"symbol": symbol}
                    )
                
                conn.commit()
                logger.info("✓ Test database cleaned")
            
            engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False

    def run_database_tests(self) -> bool:
        """Run database integration tests."""
        logger.info("Running database integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "test_db_integration.py",
            "-v",
            "--tb=short",
            "-m", "not slow"  # Skip slow tests by default
        ]
        
        if self.verbose:
            cmd.append("-s")
        
        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=not self.verbose)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Database tests failed: {e}")
            return False

    def run_api_tests(self) -> bool:
        """Run API integration tests."""
        logger.info("Running API integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "test_e2e_api.py",
            "-v",
            "--tb=short",
            "-m", "not slow"
        ]
        
        if self.verbose:
            cmd.append("-s")
        
        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=not self.verbose)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"API tests failed: {e}")
            return False

    def cleanup_test_environment(self):
        """Clean up test environment after tests."""
        logger.info("Cleaning up test environment...")
        
        try:
            # Clean test data again
            engine = create_engine(POSTGRES_URL)
            with engine.connect() as conn:
                test_patterns = ['9%', '8%', '7%'] 
                for pattern in test_patterns:
                    conn.execute(
                        text("DELETE FROM stocks WHERE symbol LIKE :pattern"),
                        {"pattern": pattern}
                    )
                conn.commit()
                logger.info("✓ Test environment cleaned up")
            engine.dispose()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        success = True
        
        # Check services unless skipped
        if not self.args.skip_setup:
            if not self.check_docker_services():
                logger.error("Docker services are not ready. Please run: docker-compose up -d")
                return False
        
        # Setup test environment
        if not self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        try:
            # Run database tests
            if not self.args.api_only:
                db_success = self.run_database_tests()
                if not db_success:
                    logger.error("Database integration tests failed")
                    success = False
                else:
                    logger.info("✓ Database integration tests passed")
            
            # Run API tests
            if not self.args.db_only:
                api_success = self.run_api_tests()
                if not api_success:
                    logger.error("API integration tests failed")
                    success = False
                else:
                    logger.info("✓ API integration tests passed")
                    
        finally:
            self.cleanup_test_environment()
        
        return success

    def generate_test_report(self) -> Dict[str, str]:
        """Generate test report with coverage and results."""
        logger.info("Generating test report...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "test_db_integration.py",
            "test_e2e_api.py", 
            "--tb=line",
            "--quiet",
            "--co"  # collect-only to get test count
        ]
        
        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent, 
                                  capture_output=True, text=True)
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }


def main():
    """Main entry point for integration test runner."""
    parser = argparse.ArgumentParser(
        description="Run integration tests against Docker services"
    )
    parser.add_argument("--db-only", action="store_true",
                       help="Run only database integration tests")
    parser.add_argument("--api-only", action="store_true", 
                       help="Run only API integration tests")
    parser.add_argument("--skip-setup", action="store_true",
                       help="Skip Docker service health checks")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--report", action="store_true",
                       help="Generate test report only")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = IntegrationTestRunner(args)
    
    if args.report:
        report = runner.generate_test_report()
        print(f"Test Report: {report}")
        return 0
    
    # Run tests
    success = runner.run_all_tests()
    
    if success:
        logger.info("🎉 All integration tests passed!")
        return 0
    else:
        logger.error("❌ Some integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())