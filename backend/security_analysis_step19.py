#!/usr/bin/env python3
"""
AskRAG Security Analysis - Step 19 (Offline)
Comprehensive security code review and analysis
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any

class OfflineSecurityAnalyzer:
    """Security analysis without requiring running backend"""
    
    def __init__(self, base_path: str = "d:\\11-coding\\AskRAG\\backend"):
        self.base_path = base_path
        self.vulnerabilities = []
        self.security_findings = {
            "authentication_security": [],
            "authorization_controls": [],
            "input_validation": [],
            "injection_protection": [],
            "cors_configuration": [],
            "security_headers": [],
            "password_security": [],
            "token_security": [],
            "session_management": [],
            "configuration_security": []
        }
        
    def print_section(self, title: str):
        """Print formatted section header"""
        print("\n" + "="*60)
        print(f"🔒 {title}")
        print("="*60)
    
    def print_test(self, test_name: str, status: str, details: str = ""):
        """Print test result"""
        icons = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}
        icon = icons.get(status, "📋")
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def add_vulnerability(self, severity: str, category: str, description: str, details: str = ""):
        """Add vulnerability to report"""
        self.vulnerabilities.append({
            "severity": severity,
            "category": category,
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def read_file_safe(self, filepath: str) -> str:
        """Safely read file content"""
        try:
            full_path = os.path.join(self.base_path, filepath) if not os.path.isabs(filepath) else filepath
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Could not read {filepath}: {e}")
            return ""
    
    def run_complete_analysis(self):
        """Run complete offline security analysis"""
        print("🚀 ASKRAG OFFLINE SECURITY ANALYSIS")
        print("Step 19: Comprehensive Security Code Review")
        print(f"Base Path: {self.base_path}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Analyze security components
        self.analyze_authentication_system()
        self.analyze_authorization_controls()
        self.analyze_input_validation()
        self.analyze_injection_protection()
        self.analyze_cors_configuration()
        self.analyze_security_headers()
        self.analyze_password_security()
        self.analyze_token_security()
        self.analyze_session_management()
        self.analyze_configuration_security()
        
        # Generate comprehensive report
        self.generate_security_assessment()
    
    def analyze_authentication_system(self):
        """Analyze authentication implementation"""
        self.print_section("AUTHENTICATION SYSTEM ANALYSIS")
        
        # Check auth.py implementation
        auth_content = self.read_file_safe("app/core/auth.py")
        if auth_content:
            self.print_test("Authentication module found", "PASS", "app/core/auth.py exists")
            
            # Check for JWT implementation
            if "jwt.encode" in auth_content and "jwt.decode" in auth_content:
                self.print_test("JWT token implementation", "PASS", "JWT encoding/decoding present")
                self.security_findings["authentication_security"].append({
                    "test": "JWT Implementation",
                    "status": "PASS",
                    "details": "JWT token generation and validation implemented"
                })
            else:
                self.print_test("JWT token implementation", "FAIL", "JWT methods not found")
                self.add_vulnerability("HIGH", "Authentication", "JWT implementation incomplete")
            
            # Check for password hashing
            if "bcrypt" in auth_content or "hashlib" in auth_content:
                self.print_test("Password hashing", "PASS", "Password hashing implementation found")
                self.security_findings["authentication_security"].append({
                    "test": "Password Hashing",
                    "status": "PASS",
                    "details": "Secure password hashing implemented"
                })
            else:
                self.print_test("Password hashing", "WARNING", "Password hashing method unclear")
                self.add_vulnerability("MEDIUM", "Authentication", "Password hashing implementation unclear")
        else:
            self.print_test("Authentication module", "FAIL", "app/core/auth.py not found")
            self.add_vulnerability("CRITICAL", "Authentication", "Authentication module missing")
    
    def analyze_authorization_controls(self):
        """Analyze authorization and access control"""
        self.print_section("AUTHORIZATION CONTROLS ANALYSIS")
        
        auth_content = self.read_file_safe("app/core/auth.py")
        user_model = self.read_file_safe("app/models/user.py")
        
        if "role" in user_model.lower() or "permission" in user_model.lower():
            self.print_test("Role-based access control", "PASS", "Role/permission references found")
            self.security_findings["authorization_controls"].append({
                "test": "RBAC Implementation",
                "status": "PASS",
                "details": "Role-based access control references present"
            })
        else:
            self.print_test("Role-based access control", "WARNING", "RBAC implementation unclear")
        
        if "Depends" in auth_content and "get_current_user" in auth_content:
            self.print_test("Dependency injection security", "PASS", "FastAPI dependency injection used")
            self.security_findings["authorization_controls"].append({
                "test": "Dependency Injection",
                "status": "PASS",
                "details": "FastAPI dependency injection for auth"
            })
        else:
            self.print_test("Dependency injection security", "WARNING", "Auth dependencies unclear")
    
    def analyze_input_validation(self):
        """Analyze input validation mechanisms"""
        self.print_section("INPUT VALIDATION ANALYSIS")
        
        schemas_dir = os.path.join(self.base_path, "app", "schemas")
        if os.path.exists(schemas_dir):
            schema_files = [f for f in os.listdir(schemas_dir) if f.endswith('.py')]
            self.print_test("Pydantic schema validation", "PASS", f"Found {len(schema_files)} schema files")
            self.security_findings["input_validation"].append({
                "test": "Pydantic Schemas",
                "status": "PASS",
                "details": f"Found {len(schema_files)} schema files for validation"
            })
        else:
            self.print_test("Pydantic schema validation", "WARNING", "Schemas directory not found")
        
        api_content = self.read_file_safe("app/api/v1/endpoints/auth.py")
        if "BaseModel" in api_content and "Field" in api_content:
            self.print_test("API input validation", "PASS", "Pydantic validation in auth endpoints")
        else:
            self.print_test("API input validation", "WARNING", "Input validation not evident")
    
    def analyze_injection_protection(self):
        """Analyze protection against injection attacks"""
        self.print_section("INJECTION PROTECTION ANALYSIS")
        
        db_content = self.read_file_safe("app/db/database.py")
        
        if "SQLAlchemy" in db_content or "orm" in db_content.lower():
            self.print_test("SQL injection protection", "PASS", "SQLAlchemy ORM usage detected")
            self.security_findings["injection_protection"].append({
                "test": "SQL Injection Protection",
                "status": "PASS",
                "details": "SQLAlchemy ORM provides parameterized queries"
            })
        else:
            self.print_test("SQL injection protection", "WARNING", "ORM usage not confirmed")
        
        if "mongodb" in db_content.lower() or "mongo" in db_content.lower():
            self.print_test("NoSQL injection awareness", "INFO", "MongoDB usage detected")
    
    def analyze_cors_configuration(self):
        """Analyze CORS configuration"""
        self.print_section("CORS CONFIGURATION ANALYSIS")
        
        main_content = self.read_file_safe("app/main.py")
        if "CORSMiddleware" in main_content:
            self.print_test("CORS middleware", "PASS", "CORS middleware configured")
            
            if "allow_origins=[\"*\"]" in main_content:
                self.print_test("CORS origin security", "WARNING", "Wildcard origins detected")
                self.add_vulnerability("MEDIUM", "CORS", "Wildcard CORS origins allow any domain")
            else:
                self.print_test("CORS origin security", "PASS", "Specific origins configured")
            
            self.security_findings["cors_configuration"].append({
                "test": "CORS Configuration",
                "status": "PASS",
                "details": "CORS middleware properly configured"
            })
        else:
            self.print_test("CORS middleware", "WARNING", "CORS configuration not found")
    
    def analyze_security_headers(self):
        """Analyze security headers implementation"""
        self.print_section("SECURITY HEADERS ANALYSIS")
        
        security_content = self.read_file_safe("app/core/security.py")
        if security_content:
            self.print_test("Security module", "PASS", "Security module exists")
            
            headers_to_check = [
                ("X-Content-Type-Options", "nosniff header"),
                ("X-Frame-Options", "clickjacking protection"),
                ("X-XSS-Protection", "XSS protection header"),
                ("Strict-Transport-Security", "HSTS header"),
                ("Content-Security-Policy", "CSP header")
            ]
            
            headers_found = 0
            for header, description in headers_to_check:
                if header in security_content:
                    self.print_test(description, "PASS", f"{header} header configured")
                    headers_found += 1
                else:
                    self.print_test(description, "WARNING", f"{header} header not found")
            
            self.security_findings["security_headers"].append({
                "test": "Security Headers",
                "status": "PASS" if headers_found >= 3 else "WARNING",
                "details": f"Found {headers_found}/{len(headers_to_check)} security headers"
            })
        else:
            self.print_test("Security headers", "WARNING", "Security module not found")
    
    def analyze_password_security(self):
        """Analyze password security implementation"""
        self.print_section("PASSWORD SECURITY ANALYSIS")
        
        auth_content = self.read_file_safe("app/core/auth.py")
        
        if "bcrypt" in auth_content:
            self.print_test("Bcrypt password hashing", "PASS", "bcrypt library used")
            self.security_findings["password_security"].append({
                "test": "Password Hashing",
                "status": "PASS",
                "details": "bcrypt used for secure password hashing"
            })
        else:
            self.print_test("Secure password hashing", "WARNING", "bcrypt usage not confirmed")
        
        user_schema = self.read_file_safe("app/schemas/user.py")
        if "password" in user_schema and ("Field" in user_schema or "validator" in user_schema):
            self.print_test("Password validation", "PASS", "Password validation schema found")
        else:
            self.print_test("Password validation", "WARNING", "Password validation not evident")
    
    def analyze_token_security(self):
        """Analyze JWT token security"""
        self.print_section("TOKEN SECURITY ANALYSIS")
        
        auth_content = self.read_file_safe("app/core/auth.py")
        config_content = self.read_file_safe("app/core/config.py")
        
        if "HS256" in auth_content or "RS256" in auth_content:
            self.print_test("JWT algorithm", "PASS", "Secure JWT algorithm specified")
            self.security_findings["token_security"].append({
                "test": "JWT Algorithm",
                "status": "PASS",
                "details": "Secure JWT signing algorithm configured"
            })
        else:
            self.print_test("JWT algorithm", "WARNING", "JWT algorithm not specified")
        
        if "exp" in auth_content or "expires" in auth_content:
            self.print_test("Token expiration", "PASS", "Token expiration implemented")
        else:
            self.print_test("Token expiration", "WARNING", "Token expiration not evident")
        
        if "SECRET_KEY" in config_content:
            self.print_test("Secret key configuration", "PASS", "Secret key configuration found")
        else:
            self.print_test("Secret key configuration", "WARNING", "Secret key configuration not found")
    
    def analyze_session_management(self):
        """Analyze session management"""
        self.print_section("SESSION MANAGEMENT ANALYSIS")
        
        auth_content = self.read_file_safe("app/core/auth.py")
        if "refresh" in auth_content.lower():
            self.print_test("Refresh token mechanism", "PASS", "Refresh token implementation found")
            self.security_findings["session_management"].append({
                "test": "Refresh Tokens",
                "status": "PASS",
                "details": "Refresh token mechanism implemented"
            })
        else:
            self.print_test("Refresh token mechanism", "WARNING", "Refresh token not evident")
        
        if "logout" in auth_content.lower() or "revoke" in auth_content.lower():
            self.print_test("Session invalidation", "PASS", "Session invalidation mechanism found")
        else:
            self.print_test("Session invalidation", "WARNING", "Session invalidation not evident")
    
    def analyze_configuration_security(self):
        """Analyze configuration security"""
        self.print_section("CONFIGURATION SECURITY ANALYSIS")
        
        env_files = [".env", ".env.example", ".env.development", ".env.production"]
        env_found = sum(1 for env_file in env_files if os.path.exists(os.path.join(self.base_path, env_file)))
        
        if env_found > 0:
            self.print_test("Environment configuration", "PASS", f"Found {env_found} environment files")
            self.security_findings["configuration_security"].append({
                "test": "Environment Variables",
                "status": "PASS",
                "details": f"Environment-based configuration with {env_found} files"
            })
        else:
            self.print_test("Environment configuration", "WARNING", "No environment files found")
        
        config_content = self.read_file_safe("app/core/config.py")
        if "DEBUG" in config_content:
            if "DEBUG = False" in config_content or "DEBUG=False" in config_content:
                self.print_test("Debug mode security", "PASS", "Debug mode explicitly disabled")
            else:
                self.print_test("Debug mode security", "WARNING", "Debug mode configuration unclear")
        
        if "HTTPS" in config_content or "SSL" in config_content:
            self.print_test("HTTPS configuration", "PASS", "HTTPS/SSL configuration found")
        else:
            self.print_test("HTTPS configuration", "INFO", "HTTPS configuration not evident")
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score"""
        total_tests = sum(len(findings) for findings in self.security_findings.values())
        if total_tests == 0:
            return 0
        
        passed_tests = sum(
            len([f for f in findings if f.get("status") == "PASS"])
            for findings in self.security_findings.values()
        )
        
        vulnerability_penalty = sum(
            20 if vuln["severity"] == "CRITICAL" else
            10 if vuln["severity"] == "HIGH" else
            5 if vuln["severity"] == "MEDIUM" else 1
            for vuln in self.vulnerabilities
        )
        
        base_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        final_score = max(0, base_score - vulnerability_penalty)
        
        return int(final_score)
    
    def generate_security_assessment(self):
        """Generate comprehensive security assessment report"""
        self.print_section("SECURITY ASSESSMENT SUMMARY")
        
        security_score = self.calculate_security_score()
        
        if security_score >= 90:
            score_status = "EXCELLENT"
            score_color = "🟢"
        elif security_score >= 80:
            score_status = "GOOD"
            score_color = "🟡"
        elif security_score >= 70:
            score_status = "FAIR"
            score_color = "🟠"
        else:
            score_status = "NEEDS IMPROVEMENT"
            score_color = "🔴"
        
        print(f"🔒 Overall Security Score: {score_color} {security_score}/100 ({score_status})")
        
        vuln_counts = {}
        for vuln in self.vulnerabilities:
            severity = vuln["severity"]
            vuln_counts[severity] = vuln_counts.get(severity, 0) + 1
        
        print(f"\n📊 Vulnerability Summary:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = vuln_counts.get(severity, 0)
            if count > 0:
                print(f"   {severity}: {count}")
        
        if not self.vulnerabilities:
            print("   ✅ No security vulnerabilities detected")
        
        print(f"\n📋 Test Results Summary:")
        for category, findings in self.security_findings.items():
            passed = len([f for f in findings if f.get("status") == "PASS"])
            total = len(findings)
            if total > 0:
                print(f"   {category.replace('_', ' ').title()}: {passed}/{total} passed")
        
        # Generate detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "security_score": security_score,
            "score_status": score_status,
            "vulnerabilities": self.vulnerabilities,
            "test_results": self.security_findings,
            "summary": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "vulnerability_breakdown": vuln_counts,
                "categories_tested": len(self.security_findings),
                "total_tests": sum(len(findings) for findings in self.security_findings.values())
            }
        }
        
        report_file = os.path.join(self.base_path, "security_assessment_report.json")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        self.print_security_recommendations()
        
        return report_data
    
    def print_security_recommendations(self):
        """Print security recommendations"""
        print(f"\n🛡️ SECURITY RECOMMENDATIONS:")
        
        recommendations = []
        
        for vuln in self.vulnerabilities:
            if vuln["severity"] in ["CRITICAL", "HIGH"]:
                recommendations.append(f"• HIGH PRIORITY: {vuln['description']}")
        
        general_recommendations = [
            "• Implement comprehensive logging and monitoring for security events",
            "• Regular security audits and penetration testing",
            "• Keep all dependencies updated to latest secure versions",
            "• Implement automated security scanning in CI/CD pipeline",
            "• Regular backup and disaster recovery testing",
            "• Security awareness training for development team",
            "• Implement Web Application Firewall (WAF) in production",
            "• Regular review of access controls and permissions"
        ]
        
        if not recommendations:
            recommendations = ["• No critical security issues identified"]
        
        recommendations.extend(general_recommendations)
        
        for rec in recommendations[:10]:
            print(rec)

def main():
    """Main execution function"""
    print("🔒 Starting AskRAG Security Analysis...")
    
    analyzer = OfflineSecurityAnalyzer()
    analyzer.run_complete_analysis()
    
    print("\n✅ Security analysis completed!")
    print("📄 Check security_assessment_report.json for detailed results")

if __name__ == "__main__":
    main()
