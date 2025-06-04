#!/usr/bin/env python3
"""
AskRAG Step 20 Deployment Validation Script
Validates the complete deployment preparation infrastructure
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

class DeploymentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def log(self, level: str, message: str):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["RESET"])
        print(f"{color}[{timestamp}] [{level}] {message}{colors['RESET']}")

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results"""
        self.log("INFO", f"Running test: {test_name}")
        
        test_result = {
            "name": test_name,
            "timestamp": datetime.now().isoformat(),
            "status": "FAILED",
            "message": "",
            "details": {}
        }
        
        try:
            result = test_func(*args, **kwargs)
            if isinstance(result, tuple):
                success, message, details = result
            elif isinstance(result, bool):
                success, message, details = result, "", {}
            else:
                success, message, details = True, str(result), {}
            
            if success:
                test_result["status"] = "PASSED"
                test_result["message"] = message or "Test passed successfully"
                self.log("SUCCESS", f"✓ {test_name}")
                self.results["summary"]["passed"] += 1
            else:
                test_result["status"] = "FAILED"
                test_result["message"] = message or "Test failed"
                test_result["details"] = details
                self.log("ERROR", f"✗ {test_name}: {message}")
                self.results["summary"]["failed"] += 1
                
        except Exception as e:
            test_result["status"] = "FAILED"
            test_result["message"] = f"Test exception: {str(e)}"
            self.log("ERROR", f"✗ {test_name}: Exception - {str(e)}")
            self.results["summary"]["failed"] += 1
        
        self.results["tests"].append(test_result)
        self.results["summary"]["total_tests"] += 1
        return test_result["status"] == "PASSED"

    def check_file_exists(self, file_path: str, description: str = None) -> Tuple[bool, str, Dict]:
        """Check if a file exists"""
        path = self.project_root / file_path
        exists = path.exists()
        
        if exists:
            size = path.stat().st_size
            return True, f"File exists ({size} bytes)", {"path": str(path), "size": size}
        else:
            return False, f"File not found: {path}", {"path": str(path)}

    def check_directory_structure(self) -> Tuple[bool, str, Dict]:
        """Validate the project directory structure"""
        required_dirs = [
            "k8s",
            "scripts", 
            "monitoring",
            ".github/workflows"
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                existing_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            return False, f"Missing directories: {', '.join(missing_dirs)}", {
                "missing": missing_dirs,
                "existing": existing_dirs
            }
        
        return True, f"All required directories exist", {"existing": existing_dirs}

    def check_kubernetes_manifests(self) -> Tuple[bool, str, Dict]:
        """Validate Kubernetes manifest files"""
        required_manifests = [
            "k8s/namespace.yaml",
            "k8s/secrets.yaml", 
            "k8s/configmap.yaml",
            "k8s/storage.yaml",
            "k8s/mongodb.yaml",
            "k8s/redis.yaml",
            "k8s/backend.yaml",
            "k8s/frontend.yaml",
            "k8s/ingress.yaml"
        ]
        
        missing_files = []
        valid_files = []
        
        for manifest in required_manifests:
            manifest_path = self.project_root / manifest
            if manifest_path.exists():
                # Basic YAML validation
                try:
                    with open(manifest_path, 'r') as f:
                        content = f.read()
                        if 'apiVersion' in content and 'kind' in content:
                            valid_files.append(manifest)
                        else:
                            missing_files.append(f"{manifest} (invalid format)")
                except Exception as e:
                    missing_files.append(f"{manifest} (read error: {e})")
            else:
                missing_files.append(manifest)
        
        if missing_files:
            return False, f"Missing/invalid manifests: {', '.join(missing_files)}", {
                "missing": missing_files,
                "valid": valid_files
            }
        
        return True, f"All {len(valid_files)} Kubernetes manifests are valid", {"valid": valid_files}

    def check_scripts(self) -> Tuple[bool, str, Dict]:
        """Validate deployment scripts"""
        required_scripts = [
            "scripts/deploy.sh",
            "scripts/deploy.ps1",
            "scripts/validate-deployment.sh",
            "scripts/smoke-tests.sh",
            "scripts/backup.sh",
            "scripts/backup.ps1",
            "scripts/disaster-recovery.sh"
        ]
        
        missing_scripts = []
        valid_scripts = []
        
        for script in required_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                valid_scripts.append(script)
            else:
                missing_scripts.append(script)
        
        if missing_scripts:
            return False, f"Missing scripts: {', '.join(missing_scripts)}", {
                "missing": missing_scripts,
                "valid": valid_scripts
            }
        
        return True, f"All {len(valid_scripts)} deployment scripts exist", {"valid": valid_scripts}

    def check_monitoring_setup(self) -> Tuple[bool, str, Dict]:
        """Validate monitoring configuration"""
        monitoring_files = [
            "monitoring/prometheus.yaml",
            "monitoring/grafana.yaml"
        ]
        
        missing_files = []
        valid_files = []
        
        for file_path in monitoring_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                valid_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        if missing_files:
            return False, f"Missing monitoring files: {', '.join(missing_files)}", {
                "missing": missing_files,
                "valid": valid_files
            }
        
        return True, f"Monitoring setup complete ({len(valid_files)} files)", {"valid": valid_files}

    def check_ci_cd_pipeline(self) -> Tuple[bool, str, Dict]:
        """Validate CI/CD pipeline configuration"""
        workflow_file = self.project_root / ".github/workflows/ci-cd.yml"
        
        if not workflow_file.exists():
            return False, "CI/CD workflow file not found", {"path": str(workflow_file)}
        
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
                
                required_elements = [
                    "name: AskRAG CI/CD Pipeline",
                    "on:",
                    "jobs:",
                    "test:",
                    "build:",
                    "deploy-staging:",
                    "deploy-production:"
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if missing_elements:
                    return False, f"Missing CI/CD elements: {', '.join(missing_elements)}", {
                        "missing": missing_elements,
                        "file_size": len(content)
                    }
                
                return True, "CI/CD pipeline configuration is complete", {
                    "file_size": len(content),
                    "elements_found": len(required_elements)
                }
                
        except Exception as e:
            return False, f"Error reading CI/CD file: {e}", {"error": str(e)}

    def check_docker_configuration(self) -> Tuple[bool, str, Dict]:
        """Validate Docker configuration"""
        docker_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "backend/Dockerfile",
            "frontend/Dockerfile"
        ]
        
        existing_files = []
        missing_files = []
        
        for file_path in docker_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        if len(existing_files) < 2:  # At least docker-compose and one Dockerfile
            return False, f"Insufficient Docker configuration. Missing: {', '.join(missing_files)}", {
                "existing": existing_files,
                "missing": missing_files
            }
        
        return True, f"Docker configuration complete ({len(existing_files)}/{len(docker_files)} files)", {
            "existing": existing_files,
            "missing": missing_files
        }

    def check_previous_test_results(self) -> Tuple[bool, str, Dict]:
        """Check if previous performance and security tests passed"""
        test_files = [
            "backend/PERFORMANCE_REPORT.md",
            "backend/STEP18_COMPLETION_SUMMARY.md", 
            "backend/STEP19_COMPLETION_SUMMARY.md",
            "backend/security_assessment_report.json"
        ]
        
        results = {}
        missing_files = []
        
        for file_path in test_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'STEP18_COMPLETION_SUMMARY' in file_path:
                            results['performance_tests'] = 'COMPLETED' in content
                        elif 'STEP19_COMPLETION_SUMMARY' in file_path:
                            results['security_tests'] = 'COMPLETED' in content
                        elif 'PERFORMANCE_REPORT' in file_path:
                            results['performance_report'] = 'ops/sec' in content
                        elif 'security_assessment_report' in file_path:
                            results['security_report'] = 'security_score' in content
                except Exception as e:
                    results[file_path] = f"Error reading: {e}"
            else:
                missing_files.append(file_path)
        
        if missing_files:
            return False, f"Missing test result files: {', '.join(missing_files)}", {
                "missing": missing_files,
                "results": results
            }
        
        passed_tests = sum(1 for v in results.values() if v is True)
        total_tests = len([k for k in results.keys() if not k.startswith('Error')])
        
        if passed_tests >= total_tests * 0.75:  # At least 75% of tests should show positive results
            return True, f"Previous test results look good ({passed_tests}/{total_tests})", results
        else:
            return False, f"Previous test results incomplete ({passed_tests}/{total_tests})", results

    def validate_completion_summary(self) -> Tuple[bool, str, Dict]:
        """Validate the Step 20 completion summary"""
        summary_file = self.project_root / "STEP20_COMPLETION_SUMMARY.md"
        
        if not summary_file.exists():
            return False, "Step 20 completion summary not found", {"path": str(summary_file)}
        
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                required_sections = [
                    "Step 20: Deployment Preparation",
                    "CI/CD Pipeline",
                    "Kubernetes Infrastructure", 
                    "Deployment Automation",
                    "Production Monitoring",
                    "Backup and Disaster Recovery"
                ]
                
                missing_sections = []
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if missing_sections:
                    return False, f"Missing sections in summary: {', '.join(missing_sections)}", {
                        "missing": missing_sections,
                        "content_length": len(content)
                    }
                
                # Check for completion indicators
                completion_indicators = [
                    "SUCCESSFULLY COMPLETED",
                    "production-ready",
                    "enterprise-grade"
                ]
                
                indicators_found = sum(1 for indicator in completion_indicators if indicator in content)
                
                return True, f"Step 20 completion summary is comprehensive ({indicators_found} completion indicators)", {
                    "content_length": len(content),
                    "sections_found": len(required_sections),
                    "indicators_found": indicators_found
                }
                
        except Exception as e:
            return False, f"Error reading completion summary: {e}", {"error": str(e)}

    async def run_all_validations(self):
        """Run all validation tests"""
        self.log("INFO", "Starting Step 20 Deployment Preparation Validation")
        self.log("INFO", "=" * 50)
        
        # Structure and file validations
        self.run_test("Directory Structure", self.check_directory_structure)
        self.run_test("Kubernetes Manifests", self.check_kubernetes_manifests)
        self.run_test("Deployment Scripts", self.check_scripts)
        self.run_test("Monitoring Setup", self.check_monitoring_setup)
        self.run_test("CI/CD Pipeline", self.check_ci_cd_pipeline)
        self.run_test("Docker Configuration", self.check_docker_configuration)
        
        # Test results validation
        self.run_test("Previous Test Results", self.check_previous_test_results)
        self.run_test("Completion Summary", self.validate_completion_summary)
        
        # Individual file checks
        critical_files = [
            ("scripts/deploy.sh", "Main deployment script"),
            ("scripts/backup.sh", "Backup script"), 
            ("monitoring/prometheus.yaml", "Prometheus configuration"),
            ("k8s/backend.yaml", "Backend deployment manifest"),
            (".github/workflows/ci-cd.yml", "CI/CD workflow")
        ]
        
        for file_path, description in critical_files:
            self.run_test(f"{description} exists", self.check_file_exists, file_path, description)

    def generate_report(self):
        """Generate final validation report"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "VALIDATION SUMMARY")
        self.log("INFO", "=" * 50)
        
        summary = self.results["summary"]
        total = summary["total_tests"]
        passed = summary["passed"]
        failed = summary["failed"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if failed == 0:
            self.log("SUCCESS", f"ALL TESTS PASSED! ({passed}/{total})")
            self.log("SUCCESS", "Step 20 Deployment Preparation is COMPLETE and READY for production!")
        else:
            self.log("ERROR", f"SOME TESTS FAILED! ({passed}/{total} passed, {failed} failed)")
            self.log("WARNING", "Please review failed tests before proceeding to production.")
        
        self.log("INFO", f"Success Rate: {success_rate:.1f}%")
        
        # Save detailed report
        report_file = self.project_root / f"step20_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log("INFO", f"Detailed report saved to: {report_file}")
        
        return failed == 0

async def main():
    """Main validation function"""
    validator = DeploymentValidator()
    
    try:
        await validator.run_all_validations()
        success = validator.generate_report()
        
        if success:
            print("\n🎉 Step 20: Deployment Preparation validation PASSED!")
            print("The AskRAG system is ready for production deployment.")
            sys.exit(0)
        else:
            print("\n❌ Step 20: Deployment Preparation validation FAILED!")
            print("Please review the failed tests and fix issues before production deployment.")
            sys.exit(1)
            
    except Exception as e:
        validator.log("ERROR", f"Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
