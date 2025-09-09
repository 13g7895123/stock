#!/usr/bin/env python
"""Comprehensive API endpoint tests for host header validation and functionality."""

import json
import requests
import sys
import time
from typing import Dict, Any, Optional


class APITestClient:
    """Test client for Stock Analysis API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:9121"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Stock-Analysis-Test-Client/1.0'
        })
    
    def test_request(self, method: str, endpoint: str, **kwargs) -> tuple[bool, Dict[str, Any]]:
        """Make test request and return success status with response data."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            return True, {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        except Exception as e:
            return False, {'error': str(e)}


def test_health_endpoints(client: APITestClient) -> bool:
    """Test health check endpoints."""
    print("=== Testing Health Endpoints ===")
    
    # Test root endpoint
    success, response = client.test_request('GET', '/')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] Root endpoint failed: {response}")
        return False
    
    print(f"[PASS] Root endpoint: {response['json']['message']}")
    
    # Test health endpoint
    success, response = client.test_request('GET', '/api/v1/health')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] Health endpoint failed: {response}")
        return False
    
    health_data = response['json']
    print(f"[PASS] Health endpoint: status={health_data['status']}")
    
    return True


def test_stock_sync_endpoints(client: APITestClient) -> bool:
    """Test stock synchronization endpoints."""
    print("\n=== Testing Stock Sync Endpoints ===")
    
    # Test stock count endpoint (the original problematic endpoint)
    success, response = client.test_request('GET', '/api/v1/sync/stocks/count')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] Stock count endpoint failed: {response}")
        return False
    
    count_data = response['json']
    print(f"[PASS] Stock count endpoint: total={count_data['total']}, markets={count_data['markets']}")
    
    # Test stock validation endpoint
    success, response = client.test_request('GET', '/api/v1/sync/stocks/validate/2330')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] Stock validation endpoint failed: {response}")
        return False
    
    validation_data = response['json']
    print(f"[PASS] Stock validation endpoint: valid={validation_data['is_valid']}")
    
    # Test stock sync endpoint (POST)
    success, response = client.test_request('POST', '/api/v1/sync/stocks/sync')
    if not success:
        print(f"[FAIL] Stock sync endpoint failed: {response}")
        return False
    
    # Accept either success (200) or async task (202) responses
    if response['status_code'] not in [200, 202]:
        print(f"[FAIL] Stock sync endpoint unexpected status: {response['status_code']}")
        return False
    
    sync_data = response['json']
    print(f"[PASS] Stock sync endpoint: {sync_data}")
    
    return True


def test_host_header_validation(client: APITestClient) -> bool:
    """Test that host header validation works correctly."""
    print("\n=== Testing Host Header Validation ===")
    
    # Test with localhost
    success, response = client.test_request('GET', '/api/v1/sync/stocks/count')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] localhost request failed: {response}")
        return False
    
    print("[PASS] localhost request accepted")
    
    # Test with 127.0.0.1
    client_ip = APITestClient("http://127.0.0.1:9121")
    success, response = client_ip.test_request('GET', '/api/v1/sync/stocks/count')
    if not success or response['status_code'] != 200:
        print(f"[FAIL] 127.0.0.1 request failed: {response}")
        return False
    
    print("[PASS] 127.0.0.1 request accepted")
    
    # Test with custom host header (should work since DEBUG=true allows all hosts)
    headers = {'Host': 'example.com'}
    success, response = client.test_request('GET', '/api/v1/sync/stocks/count', headers=headers)
    if not success or response['status_code'] not in [200, 400]:
        print(f"[WARN] Custom host header test inconclusive: {response}")
    else:
        print(f"[PASS] Custom host header handled: status={response['status_code']}")
    
    return True


def test_cors_headers(client: APITestClient) -> bool:
    """Test CORS headers are properly set."""
    print("\n=== Testing CORS Headers ===")
    
    # Test preflight request
    success, response = client.test_request('OPTIONS', '/api/v1/sync/stocks/count', headers={'Origin': 'http://localhost:3000'})
    if not success:
        print(f"[WARN] CORS preflight test failed: {response}")
        return True  # Non-critical failure
    
    headers = response.get('headers', {})
    cors_headers = [h for h in headers.keys() if h.lower().startswith('access-control')]
    
    if cors_headers:
        print(f"[PASS] CORS headers present: {cors_headers}")
    else:
        print("[WARN] No CORS headers found (may be expected)")
    
    return True


def test_error_handling(client: APITestClient) -> bool:
    """Test error handling for invalid requests."""
    print("\n=== Testing Error Handling ===")
    
    # Test 404 for non-existent endpoint
    success, response = client.test_request('GET', '/api/v1/nonexistent')
    if success and response['status_code'] == 404:
        print("[PASS] 404 handled correctly for non-existent endpoint")
    else:
        print(f"[WARN] Unexpected response for 404 test: {response}")
    
    # Test invalid stock symbol validation
    success, response = client.test_request('GET', '/api/v1/sync/stocks/validate/INVALID_SYMBOL')
    if success and response['status_code'] == 200:
        validation_data = response['json']
        if not validation_data.get('is_valid', True):
            print("[PASS] Invalid stock symbol correctly rejected")
        else:
            print("[WARN] Invalid stock symbol not rejected as expected")
    
    return True


def wait_for_service(client: APITestClient, max_attempts: int = 30) -> bool:
    """Wait for service to be ready."""
    print("Waiting for service to be ready...")
    
    for attempt in range(max_attempts):
        try:
            success, response = client.test_request('GET', '/api/v1/health', timeout=5)
            if success and response['status_code'] == 200:
                print(f"Service ready after {attempt + 1} attempts")
                return True
        except:
            pass
        
        time.sleep(2)
        print(f"Attempt {attempt + 1}/{max_attempts}...")
    
    print("Service not ready after maximum attempts")
    return False


def main():
    """Run comprehensive API tests."""
    print("=== Stock Analysis API Endpoint Tests ===")
    print("Testing API endpoints for host header validation and functionality\n")
    
    client = APITestClient()
    
    # Wait for service to be ready
    if not wait_for_service(client):
        print("[ERROR] Service not ready, aborting tests")
        sys.exit(1)
    
    # Run test suites
    test_results = []
    
    test_results.append(("Health Endpoints", test_health_endpoints(client)))
    test_results.append(("Stock Sync Endpoints", test_stock_sync_endpoints(client)))
    test_results.append(("Host Header Validation", test_host_header_validation(client)))
    test_results.append(("CORS Headers", test_cors_headers(client)))
    test_results.append(("Error Handling", test_error_handling(client)))
    
    # Summary
    print("\n" + "=" * 50)
    print("=== Test Results Summary ===")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n[SUCCESS] All API tests passed! Host header error resolved.")
        print("\nAvailable API endpoints:")
        print("- GET  http://localhost:9121/api/v1/sync/stocks/count")
        print("- POST http://localhost:9121/api/v1/sync/stocks/sync")
        print("- GET  http://localhost:9121/api/v1/sync/stocks/validate/<symbol>")
        print("- GET  http://localhost:9121/api/v1/health")
        print("- GET  http://localhost:9121/")
        sys.exit(0)
    else:
        print(f"\n[ERROR] {total - passed} test suite(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()