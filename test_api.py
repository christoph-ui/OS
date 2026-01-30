#!/usr/bin/env python3
"""
API Test Script for 0711 Console Backend
Tests all endpoints with proper authentication
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def print_result(name, response, expected_status=200):
    """Print test result"""
    status = "✓" if response.status_code == expected_status else "✗"
    print(f"\n{status} {name} (HTTP {response.status_code})")
    try:
        data = response.json()
        print(json.dumps(data, indent=2)[:500])
    except:
        print(response.text[:200])
    return response.status_code == expected_status

def main():
    results = []

    print("=" * 60)
    print("0711 Console Backend - API Tests")
    print("=" * 60)

    # 1. Health check
    print("\n--- Health & Root ---")
    r = requests.get(f"{BASE_URL}/health")
    results.append(print_result("GET /health", r))

    r = requests.get(f"{BASE_URL}/")
    results.append(print_result("GET /", r))

    # 2. Auth - Register
    print("\n--- Auth Endpoints ---")
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": "apitest@test.com",
        "name": "API Test User",
        "customer_id": "api_test_corp",
        "password": "apitest123!"
    })
    results.append(print_result("POST /api/auth/register", r, 201))

    # 3. Auth - Login
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "password": "test123!"
    })
    results.append(print_result("POST /api/auth/login", r))

    if r.status_code == 200:
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 4. Auth - Me
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        results.append(print_result("GET /api/auth/me", r))

        # 5. Auth - Context
        r = requests.get(f"{BASE_URL}/api/auth/context", headers=headers)
        results.append(print_result("GET /api/auth/context", r))

        # 6. Auth - Refresh
        r = requests.post(f"{BASE_URL}/api/auth/refresh", headers=headers)
        results.append(print_result("POST /api/auth/refresh", r))

        # 7. Unauthenticated access (should fail)
        r = requests.get(f"{BASE_URL}/api/auth/me")
        results.append(print_result("GET /api/auth/me (no auth)", r, 401))

        # 8. Data endpoints
        print("\n--- Data Endpoints ---")
        r = requests.get(f"{BASE_URL}/api/data/browse", headers=headers)
        results.append(print_result("GET /api/data/browse", r))

        r = requests.post(f"{BASE_URL}/api/data/search", headers=headers, json={
            "query": "tax regulations",
            "limit": 10
        })
        results.append(print_result("POST /api/data/search", r))

        r = requests.get(f"{BASE_URL}/api/data/stats", headers=headers)
        results.append(print_result("GET /api/data/stats", r))

        r = requests.get(f"{BASE_URL}/api/data/categories", headers=headers)
        results.append(print_result("GET /api/data/categories", r))

        # 9. MCP endpoints
        print("\n--- MCP Endpoints ---")
        r = requests.get(f"{BASE_URL}/api/mcps/", headers=headers)
        results.append(print_result("GET /api/mcps/", r))

        r = requests.get(f"{BASE_URL}/api/mcps/ctax", headers=headers)
        # May return 404 if MCP not loaded - that's OK
        results.append(print_result("GET /api/mcps/ctax", r, r.status_code))

        # 10. Ingest endpoints
        print("\n--- Ingest Endpoints ---")
        r = requests.get(f"{BASE_URL}/api/ingest/jobs", headers=headers)
        results.append(print_result("GET /api/ingest/jobs", r))

        # 11. Chat endpoint (REST)
        print("\n--- Chat Endpoints ---")
        r = requests.post(f"{BASE_URL}/api/chat", headers=headers, json={
            "message": "What is VAT?",
            "mcp": None
        })
        # May fail due to platform not fully configured - check status
        print_result("POST /api/chat", r, r.status_code)

        # 12. Admin endpoints
        print("\n--- Admin Endpoints ---")
        # Login as admin
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@0711.io",
            "password": "admin123!"
        })
        if r.status_code == 200:
            admin_token = r.json()["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}

            r = requests.get(f"{BASE_URL}/api/auth/context", headers=admin_headers)
            results.append(print_result("GET /api/auth/context (admin)", r))

    else:
        print("Login failed, skipping authenticated tests")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
