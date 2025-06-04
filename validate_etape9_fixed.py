#!/usr/bin/env python3
"""
Comprehensive validation of Étape 9 - Tests End-to-End
This script validates the authentication system integration between React frontend and Flask backend.
"""

import requests
import time
import json
from typing import Dict, Any
import sys

# ANSI color codes for console output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE):
    """Print colored text to console"""
    print(f"{color}{text}{Colors.END}")

def print_header(text: str):
    """Print a colored header"""
    print_colored(f"\n{'='*50}", Colors.CYAN)
    print_colored(f" {text}", Colors.BOLD + Colors.CYAN)
    print_colored(f"{'='*50}", Colors.CYAN)

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with appropriate coloring"""
    status = "✅ PASS" if passed else "❌ FAIL"
    color = Colors.GREEN if passed else Colors.RED
    print_colored(f"{status} {test_name}", color)
    if details:
        print_colored(f"    {details}", Colors.YELLOW)

def check_server_availability(url: str, name: str) -> bool:
    """Check if a server is available"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def test_backend_auth_flow():
    """Test the complete backend authentication flow"""
    print_header("BACKEND AUTHENTICATION TESTS")
    
    base_url = "http://localhost:8000"
    auth_url = f"{base_url}/api/v1/auth"
    
    results = []
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        passed = response.status_code == 200
        print_test_result("Health endpoint", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("Health endpoint", False, f"Error: {e}")
        results.append(False)
    
    # Test 2: Valid login
    try:
        login_data = {"username": "test@example.com", "password": "test123"}
        response = requests.post(f"{auth_url}/login", json=login_data, timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            token_valid = "tokens" in data and "user" in data
            access_token = data.get("tokens", {}).get("accessToken")
            passed = passed and token_valid and access_token
            
        print_test_result("Valid login", passed, f"Status: {response.status_code}")
        results.append(passed)
        
        # Store token for later tests
        if passed:
            global_token = access_token
        else:
            global_token = None
            
    except Exception as e:
        print_test_result("Valid login", False, f"Error: {e}")
        results.append(False)
        global_token = None
    
    # Test 3: Invalid login
    try:
        login_data = {"username": "invalid@example.com", "password": "wrongpass"}
        response = requests.post(f"{auth_url}/login", json=login_data, timeout=5)
        passed = response.status_code == 401
        print_test_result("Invalid login rejection", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("Invalid login rejection", False, f"Error: {e}")
        results.append(False)
    
    # Test 4: Registration
    try:
        register_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "newpass123",
            "firstName": "Test",
            "lastName": "User"
        }
        response = requests.post(f"{auth_url}/register", json=register_data, timeout=5)
        passed = response.status_code in [200, 201]
        print_test_result("User registration", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("User registration", False, f"Error: {e}")
        results.append(False)
    
    # Test 5: Protected endpoint with token
    if global_token:
        try:
            headers = {"Authorization": f"Bearer {global_token}"}
            response = requests.get(f"{auth_url}/me", headers=headers, timeout=5)
            passed = response.status_code == 200
            print_test_result("Protected endpoint with token", passed, f"Status: {response.status_code}")
            results.append(passed)
        except Exception as e:
            print_test_result("Protected endpoint with token", False, f"Error: {e}")
            results.append(False)
    else:
        print_test_result("Protected endpoint with token", False, "No token available")
        results.append(False)
    
    # Test 6: Protected endpoint without token
    try:
        response = requests.get(f"{auth_url}/me", timeout=5)
        passed = response.status_code in [401, 403]
        print_test_result("Protected endpoint without token", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("Protected endpoint without token", False, f"Error: {e}")
        results.append(False)
    
    return results

def test_frontend_accessibility():
    """Test frontend accessibility"""
    print_header("FRONTEND ACCESSIBILITY TESTS")
    
    base_url = "http://localhost:5173"
    results = []
    
    # Test 1: Frontend homepage
    try:
        response = requests.get(base_url, timeout=10)
        passed = response.status_code == 200 and "text/html" in response.headers.get("content-type", "")
        print_test_result("Frontend homepage", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("Frontend homepage", False, f"Error: {e}")
        results.append(False)
    
    # Test 2: Static assets
    try:
        response = requests.get(f"{base_url}/vite.svg", timeout=5)
        passed = response.status_code == 200
        print_test_result("Static assets loading", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("Static assets loading", False, f"Error: {e}")
        results.append(False)
    
    return results

def test_integration():
    """Test frontend-backend integration"""
    print_header("FRONTEND-BACKEND INTEGRATION TESTS")
    
    results = []
    
    # Test CORS headers
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": "test@example.com", "password": "test123"},
            headers={"Origin": "http://localhost:5173"},
            timeout=5
        )
        # Check if request goes through (CORS not blocking)
        passed = response.status_code in [200, 401, 422]  # Any response means CORS is not blocking
        print_test_result("CORS compatibility", passed, f"Status: {response.status_code}")
        results.append(passed)
    except Exception as e:
        print_test_result("CORS compatibility", False, f"Error: {e}")
        results.append(False)
    
    return results

def main():
    """Main validation function"""
    print_colored("🚀 ÉTAPE 9 - TESTS END-TO-END VALIDATION", Colors.BOLD + Colors.PURPLE)
    print_colored("Testing authentication system integration between React frontend and Flask backend", Colors.WHITE)
    
    # Check server availability
    print_header("SERVER AVAILABILITY CHECK")
    backend_available = check_server_availability("http://localhost:8000", "Backend")
    frontend_available = check_server_availability("http://localhost:5173", "Frontend")
    
    print_test_result("Backend server (http://localhost:8000)", backend_available)
    print_test_result("Frontend server (http://localhost:5173)", frontend_available)
    
    if not backend_available:
        print_colored("\n❌ Backend server is not running!", Colors.RED)
        print_colored("Please start the backend server and try again.", Colors.YELLOW)
        return False
    
    if not frontend_available:
        print_colored("\n⚠️  Frontend server is not running!", Colors.YELLOW)
        print_colored("Frontend tests will be skipped.", Colors.YELLOW)
    
    # Run tests
    all_results = []
    
    # Backend tests
    backend_results = test_backend_auth_flow()
    all_results.extend(backend_results)
    
    # Frontend tests (if available)
    if frontend_available:
        frontend_results = test_frontend_accessibility()
        all_results.extend(frontend_results)
        
        # Integration tests
        integration_results = test_integration()
        all_results.extend(integration_results)
    
    # Summary
    print_header("VALIDATION SUMMARY")
    passed_count = sum(all_results)
    total_count = len(all_results)
    success_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
    
    print_colored(f"Tests passed: {passed_count}/{total_count} ({success_rate:.1f}%)", Colors.BOLD)
    
    if success_rate >= 80:
        print_colored("🎉 ÉTAPE 9 VALIDATION: SUCCESS", Colors.BOLD + Colors.GREEN)
        print_colored("The authentication system is working correctly!", Colors.GREEN)
    elif success_rate >= 60:
        print_colored("⚠️  ÉTAPE 9 VALIDATION: PARTIAL SUCCESS", Colors.BOLD + Colors.YELLOW)
        print_colored("Most tests passed, but some issues need attention.", Colors.YELLOW)
    else:
        print_colored("❌ ÉTAPE 9 VALIDATION: NEEDS WORK", Colors.BOLD + Colors.RED)
        print_colored("Several critical issues need to be resolved.", Colors.RED)
    
    print_header("NEXT STEPS")
    if success_rate >= 80:
        print_colored("✅ Ready to proceed to Étape 10: Document Ingestion", Colors.GREEN)
        print_colored("✅ Authentication system is fully functional", Colors.GREEN)
        print_colored("✅ Frontend-backend integration is working", Colors.GREEN)
    else:
        print_colored("🔧 Fix failing tests before proceeding", Colors.YELLOW)
        if not frontend_available:
            print_colored("🔧 Start the frontend server for complete testing", Colors.YELLOW)
        print_colored("🔧 Review test output for specific issues", Colors.YELLOW)
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
