#!/usr/bin/env python3
"""
Environment Validation Script for AskRAG
Validates environment variables and configuration for all environments
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class ValidationResult:
    """Result of environment validation"""
    is_valid: bool
    environment: str
    missing_vars: List[str]
    invalid_vars: List[str]
    warnings: List[str]
    errors: List[str]

class EnvironmentValidator:
    """Validates environment configurations"""
    
    # Required variables for each environment
    REQUIRED_BACKEND_VARS = {
        'development': [
            'ENVIRONMENT', 'DEBUG', 'SECRET_KEY', 'JWT_SECRET_KEY',
            'MONGODB_URL', 'MONGODB_DB_NAME', 'PROJECT_NAME'
        ],
        'staging': [
            'ENVIRONMENT', 'DEBUG', 'SECRET_KEY', 'JWT_SECRET_KEY',
            'MONGODB_URL', 'MONGODB_DB_NAME', 'PROJECT_NAME',
            'REDIS_URL', 'CORS_ORIGINS'
        ],
        'production': [
            'ENVIRONMENT', 'DEBUG', 'SECRET_KEY', 'JWT_SECRET_KEY',
            'MONGODB_URL', 'MONGODB_DB_NAME', 'PROJECT_NAME',
            'REDIS_URL', 'CORS_ORIGINS', 'SENTRY_DSN'
        ]
    }
    
    REQUIRED_FRONTEND_VARS = {
        'development': [
            'VITE_API_BASE_URL', 'VITE_APP_NAME', 'VITE_MAX_FILE_SIZE'
        ],
        'staging': [
            'VITE_API_BASE_URL', 'VITE_APP_NAME', 'VITE_MAX_FILE_SIZE',
            'VITE_ANALYTICS_ENABLED'
        ],
        'production': [
            'VITE_API_BASE_URL', 'VITE_APP_NAME', 'VITE_MAX_FILE_SIZE',
            'VITE_ANALYTICS_ENABLED', 'VITE_SENTRY_DSN'
        ]
    }
    
    # Validation patterns
    VALIDATION_PATTERNS = {
        'MONGODB_URL': r'^mongodb://.*',
        'REDIS_URL': r'^redis://.*',
        'VITE_API_BASE_URL': r'^https?://.*',
        'JWT_SECRET_KEY': r'^.{32,}$',  # At least 32 characters
        'SECRET_KEY': r'^.{32,}$',  # At least 32 characters
        'OPENAI_API_KEY': r'^sk-.*',
        'SENTRY_DSN': r'^https://.*@.*\.ingest\.sentry\.io/.*',
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def load_env_file(self, file_path: Path) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        if not file_path.exists():
            return env_vars
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return env_vars
    
    def validate_var_pattern(self, var_name: str, value: str) -> bool:
        """Validate variable against pattern"""
        pattern = self.VALIDATION_PATTERNS.get(var_name)
        if pattern:
            return bool(re.match(pattern, value))
        return True
    
    def check_secrets_placeholders(self, env_vars: Dict[str, str]) -> List[str]:
        """Check for unresolved secret placeholders"""
        placeholders = []
        for key, value in env_vars.items():
            if value.startswith('${') and value.endswith('}'):
                placeholders.append(f"{key}={value}")
        return placeholders
    
    def validate_backend_env(self, environment: str) -> ValidationResult:
        """Validate backend environment configuration"""
        env_file = self.project_root / 'backend' / f'.env.{environment}'
        env_vars = self.load_env_file(env_file)
        
        required_vars = self.REQUIRED_BACKEND_VARS.get(environment, [])
        missing_vars = [var for var in required_vars if var not in env_vars]
        
        invalid_vars = []
        warnings = []
        errors = []
        
        # Check file exists
        if not env_file.exists():
            errors.append(f"Environment file not found: {env_file}")
            return ValidationResult(False, environment, missing_vars, invalid_vars, warnings, errors)
        
        # Validate patterns
        for var_name, value in env_vars.items():
            if not self.validate_var_pattern(var_name, value):
                invalid_vars.append(f"{var_name}={value}")
        
        # Check for unresolved secrets in production/staging
        if environment in ['staging', 'production']:
            placeholders = self.check_secrets_placeholders(env_vars)
            if placeholders:
                warnings.append(f"Unresolved secrets found: {', '.join(placeholders)}")
        
        # Environment-specific validations
        if environment == 'production':
            if env_vars.get('DEBUG', '').lower() == 'true':
                errors.append("DEBUG should be False in production")
            if env_vars.get('LOG_LEVEL', '').upper() not in ['WARNING', 'ERROR']:
                warnings.append("Consider using WARNING or ERROR log level in production")
        
        is_valid = len(missing_vars) == 0 and len(invalid_vars) == 0 and len(errors) == 0
        
        return ValidationResult(is_valid, environment, missing_vars, invalid_vars, warnings, errors)
    
    def validate_frontend_env(self, environment: str) -> ValidationResult:
        """Validate frontend environment configuration"""
        env_file = self.project_root / 'frontend' / f'.env.{environment}'
        env_vars = self.load_env_file(env_file)
        
        required_vars = self.REQUIRED_FRONTEND_VARS.get(environment, [])
        missing_vars = [var for var in required_vars if var not in env_vars]
        
        invalid_vars = []
        warnings = []
        errors = []
        
        # Check file exists
        if not env_file.exists():
            errors.append(f"Environment file not found: {env_file}")
            return ValidationResult(False, environment, missing_vars, invalid_vars, warnings, errors)
        
        # Validate patterns
        for var_name, value in env_vars.items():
            if not self.validate_var_pattern(var_name, value):
                invalid_vars.append(f"{var_name}={value}")
        
        # Check for unresolved secrets
        if environment in ['staging', 'production']:
            placeholders = self.check_secrets_placeholders(env_vars)
            if placeholders:
                warnings.append(f"Unresolved secrets found: {', '.join(placeholders)}")
        
        is_valid = len(missing_vars) == 0 and len(invalid_vars) == 0 and len(errors) == 0
        
        return ValidationResult(is_valid, environment, missing_vars, invalid_vars, warnings, errors)
    
    def validate_all_environments(self) -> Dict[str, Dict[str, ValidationResult]]:
        """Validate all environments for both backend and frontend"""
        results = {
            'backend': {},
            'frontend': {}
        }
        
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            results['backend'][env] = self.validate_backend_env(env)
            results['frontend'][env] = self.validate_frontend_env(env)
        
        return results
    
    def print_results(self, results: Dict[str, Dict[str, ValidationResult]]):
        """Print validation results in a formatted way"""
        print("🔍 AskRAG Environment Validation Results")
        print("=" * 50)
        
        total_valid = 0
        total_configs = 0
        
        for component, env_results in results.items():
            print(f"\n📦 {component.upper()} ENVIRONMENTS:")
            print("-" * 30)
            
            for env_name, result in env_results.items():
                total_configs += 1
                status = "✅ VALID" if result.is_valid else "❌ INVALID"
                print(f"\n{env_name.upper()}: {status}")
                
                if result.is_valid:
                    total_valid += 1
                    print("  All required variables present and valid")
                
                if result.missing_vars:
                    print(f"  Missing variables: {', '.join(result.missing_vars)}")
                
                if result.invalid_vars:
                    print(f"  Invalid variables: {', '.join(result.invalid_vars)}")
                
                if result.warnings:
                    print("  Warnings:")
                    for warning in result.warnings:
                        print(f"    ⚠️  {warning}")
                
                if result.errors:
                    print("  Errors:")
                    for error in result.errors:
                        print(f"    ❌ {error}")
        
        print(f"\n📊 SUMMARY:")
        print(f"Valid configurations: {total_valid}/{total_configs}")
        print(f"Success rate: {(total_valid/total_configs)*100:.1f}%")
        
        if total_valid == total_configs:
            print("\n🎉 All environment configurations are valid!")
            return True
        else:
            print(f"\n⚠️  {total_configs - total_valid} configuration(s) need attention")
            return False

def main():
    """Main validation function"""
    # Get project root from script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent  # Go up one level from scripts/ to project root
    validator = EnvironmentValidator(project_root)
    
    print("Starting AskRAG environment validation...")
    results = validator.validate_all_environments()
    success = validator.print_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
