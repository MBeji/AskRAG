#!/usr/bin/env python3
"""
Validation Script for Étape 8: Frontend Authentication Integration
Tests the integration between React frontend and Flask backend
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class AskRAGIntegrationValidator:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5173"
        self.test_results = []
        
    def print_status(self, message, status="INFO"):
        colors = {
            "INFO": bcolors.OKBLUE,
            "SUCCESS": bcolors.OKGREEN,
            "WARNING": bcolors.WARNING,
            "ERROR": bcolors.FAIL,
            "HEADER": bcolors.HEADER
        }
        print(f"{colors.get(status, '')}{message}{bcolors.ENDC}")
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            self.print_status("🔍 Testing backend health...", "INFO")
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.print_status("✅ Backend health check passed", "SUCCESS")
                    return True
                else:
                    self.print_status("❌ Backend unhealthy response", "ERROR")
                    return False
            else:
                self.print_status(f"❌ Backend health check failed: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Backend connection failed: {str(e)}", "ERROR")
            return False
    
    def test_backend_auth_endpoints(self):
        """Test authentication endpoints"""
        results = {}
        
        # Test login endpoint
        try:
            self.print_status("🔐 Testing login endpoint...", "INFO")
            login_data = {
                "email": "test@example.com",
                "password": "test123"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "tokens" in data and "user" in data:
                    self.print_status("✅ Login endpoint working", "SUCCESS")
                    results["login"] = True
                    results["access_token"] = data["tokens"]["accessToken"]
                else:
                    self.print_status("❌ Login response missing required fields", "ERROR")
                    results["login"] = False
            else:
                self.print_status(f"❌ Login failed: {response.status_code}", "ERROR")
                results["login"] = False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Login test failed: {str(e)}", "ERROR")
            results["login"] = False
        
        # Test register endpoint
        try:
            self.print_status("📝 Testing register endpoint...", "INFO")
            register_data = {
                "email": f"testuser_{int(time.time())}@example.com",
                "password": "newpassword123",
                "firstName": "Test",
                "lastName": "User"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/auth/register",
                json=register_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "tokens" in data and "user" in data:
                    self.print_status("✅ Register endpoint working", "SUCCESS")
                    results["register"] = True
                else:
                    self.print_status("❌ Register response missing required fields", "ERROR")
                    results["register"] = False
            else:
                self.print_status(f"❌ Register failed: {response.status_code}", "ERROR")
                results["register"] = False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Register test failed: {str(e)}", "ERROR")
            results["register"] = False
        
        return results
    
    def test_frontend_availability(self):
        """Test if frontend is accessible"""
        try:
            self.print_status("🌐 Testing frontend availability...", "INFO")
            response = requests.get(self.frontend_url, timeout=5)
            
            if response.status_code == 200:
                self.print_status("✅ Frontend accessible", "SUCCESS")
                return True
            else:
                self.print_status(f"❌ Frontend not accessible: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Frontend connection failed: {str(e)}", "ERROR")
            return False
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            self.print_status("🔗 Testing CORS configuration...", "INFO")
            
            # Test preflight request
            headers = {
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(
                f"{self.backend_url}/api/v1/auth/login",
                headers=headers,
                timeout=5
            )
            
            cors_headers = response.headers
            
            if 'Access-Control-Allow-Origin' in cors_headers:
                allowed_origin = cors_headers['Access-Control-Allow-Origin']
                if allowed_origin == '*' or 'localhost:5173' in allowed_origin:
                    self.print_status("✅ CORS properly configured", "SUCCESS")
                    return True
                else:
                    self.print_status(f"⚠️ CORS origin mismatch: {allowed_origin}", "WARNING")
                    return False
            else:
                self.print_status("❌ CORS headers missing", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ CORS test failed: {str(e)}", "ERROR")
            return False
    
    def validate_integration(self):
        """Run complete integration validation"""
        self.print_status("🚀 AskRAG Integration Validation - Étape 8", "HEADER")
        self.print_status("=" * 50, "HEADER")
        
        # Test results tracking
        tests_passed = 0
        total_tests = 0
        
        # Backend tests
        self.print_status("\n📡 BACKEND TESTS", "HEADER")
        total_tests += 1
        if self.test_backend_health():
            tests_passed += 1
        
        # Auth endpoints
        total_tests += 2
        auth_results = self.test_backend_auth_endpoints()
        if auth_results.get("login"):
            tests_passed += 1
        if auth_results.get("register"):
            tests_passed += 1
        
        # Frontend tests
        self.print_status("\n🌐 FRONTEND TESTS", "HEADER")
        total_tests += 1
        if self.test_frontend_availability():
            tests_passed += 1
        
        # Integration tests
        self.print_status("\n🔗 INTEGRATION TESTS", "HEADER")
        total_tests += 1
        if self.test_cors_configuration():
            tests_passed += 1
        
        # Final results
        self.print_status("\n" + "=" * 50, "HEADER")
        self.print_status(f"📊 RESULTS: {tests_passed}/{total_tests} tests passed", "HEADER")
        
        if tests_passed == total_tests:
            self.print_status("🎉 ALL TESTS PASSED - Integration successful!", "SUCCESS")
            self.print_status("✅ Étape 8 VALIDATED", "SUCCESS")
            return True
        else:
            self.print_status(f"❌ {total_tests - tests_passed} tests failed", "ERROR")
            self.print_status("🔧 Please check the failed components", "WARNING")
            return False

def main():
    """Main validation function"""
    validator = AskRAGIntegrationValidator()
    
    try:
        success = validator.validate_integration()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        validator.print_status("\n⚠️ Validation interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        validator.print_status(f"\n❌ Validation failed with error: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
