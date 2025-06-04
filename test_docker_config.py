#!/usr/bin/env python3
"""
Quick Docker Configuration Test for AskRAG
Tests if all Docker files are properly configured
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_status(message, status="info"):
    colors = {
        "info": "\033[94m",
        "success": "\033[92m", 
        "warning": "\033[93m",
        "error": "\033[91m"
    }
    end_color = "\033[0m"
    print(f"{colors.get(status, '')}{message}{end_color}")

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print_status(f"✅ {description}: {file_path}", "success")
        return True
    else:
        print_status(f"❌ {description}: {file_path}", "error")
        return False

def check_docker_available():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"✅ Docker available: {result.stdout.strip()}", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("❌ Docker not available", "error")
    return False

def check_docker_compose_available():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"✅ Docker Compose available: {result.stdout.strip()}", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("❌ Docker Compose not available", "error")
    return False

def validate_docker_compose_syntax(compose_file):
    """Validate Docker Compose file syntax"""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "config"], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_status(f"✅ {compose_file} syntax valid", "success")
            return True
        else:
            print_status(f"❌ {compose_file} syntax invalid: {result.stderr}", "error")
            return False
    except Exception as e:
        print_status(f"❌ Error validating {compose_file}: {e}", "error")
        return False

def main():
    print_status("🐳 AskRAG Docker Configuration Test", "info")
    print_status("=" * 50, "info")
    
    # Project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    all_tests_passed = True
    
    # Check Docker availability
    print_status("\n📋 Checking Docker availability...", "info")
    if not check_docker_available():
        all_tests_passed = False
    if not check_docker_compose_available():
        all_tests_passed = False
    
    # Check Docker files
    print_status("\n📋 Checking Docker configuration files...", "info")
    
    docker_files = [
        ("docker-compose.yml", "Main Docker Compose file"),
        ("docker-compose.dev.yml", "Development Docker Compose file"),
        (".env.docker", "Production environment file"),
        (".env.docker.dev", "Development environment file"),
        ("backend/Dockerfile", "Backend production Dockerfile"),
        ("backend/Dockerfile.dev", "Backend development Dockerfile"),
        ("backend/.dockerignore", "Backend Docker ignore file"),
        ("frontend/Dockerfile", "Frontend production Dockerfile"),
        ("frontend/Dockerfile.dev", "Frontend development Dockerfile"),
        ("frontend/.dockerignore", "Frontend Docker ignore file"),
        ("frontend/nginx.conf", "Frontend Nginx configuration"),
        ("scripts/mongo-init.js", "MongoDB initialization script"),
        ("scripts/docker-helper.sh", "Docker helper script (Linux)"),
        ("scripts/docker-helper.ps1", "Docker helper script (Windows)")
    ]
    
    for file_path, description in docker_files:
        if not check_file_exists(file_path, description):
            all_tests_passed = False
    
    # Check Docker Compose syntax (if Docker is available)
    if check_docker_available() and check_docker_compose_available():
        print_status("\n📋 Validating Docker Compose syntax...", "info")
        
        compose_files = ["docker-compose.yml", "docker-compose.dev.yml"]
        for compose_file in compose_files:
            if os.path.exists(compose_file):
                if not validate_docker_compose_syntax(compose_file):
                    all_tests_passed = False
    
    # Check required dependencies
    print_status("\n📋 Checking backend requirements...", "info")
    requirements_file = "backend/requirements.txt"
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            requirements = f.read()
            required_packages = ["fastapi", "uvicorn", "motor", "pymongo"]
            for package in required_packages:
                if package in requirements:
                    print_status(f"✅ {package} found in requirements.txt", "success")
                else:
                    print_status(f"❌ {package} missing from requirements.txt", "error")
                    all_tests_passed = False
    
    # Check frontend package.json
    print_status("\n📋 Checking frontend dependencies...", "info")
    package_file = "frontend/package.json"
    if os.path.exists(package_file):
        try:
            with open(package_file, 'r') as f:
                package_data = json.load(f)
                dependencies = package_data.get('dependencies', {})
                required_packages = ["react", "vite", "axios", "@tanstack/react-query"]
                for package in required_packages:
                    if package in dependencies:
                        print_status(f"✅ {package} found in package.json", "success")
                    else:
                        print_status(f"❌ {package} missing from package.json", "error")
                        all_tests_passed = False
        except json.JSONDecodeError:
            print_status("❌ Invalid package.json format", "error")
            all_tests_passed = False
    
    # Final result
    print_status("\n" + "=" * 50, "info")
    if all_tests_passed:
        print_status("🎉 All Docker configuration tests passed!", "success")
        print_status("\n📝 Next steps:", "info")
        print_status("1. Configure your environment variables in .env files", "info")
        print_status("2. Run: docker-compose -f docker-compose.dev.yml up --build", "info")
        print_status("3. Access frontend at http://localhost:5173", "info")
        print_status("4. Access backend at http://localhost:8000", "info")
        return True
    else:
        print_status("❌ Some Docker configuration tests failed!", "error")
        print_status("Please fix the issues above before proceeding.", "warning")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
