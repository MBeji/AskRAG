#!/bin/bash
# Environment Setup Script for AskRAG
# Helps setup environment variables for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(dirname "$(dirname "$(realpath "$0")")")"

echo -e "${BLUE}🔧 AskRAG Environment Setup${NC}"
echo "==============================="

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to copy environment template
copy_env_template() {
    local component=$1
    local environment=$2
    local source_file="$PROJECT_ROOT/$component/.env.$environment"
    local target_file="$PROJECT_ROOT/$component/.env"
    
    if [[ -f "$source_file" ]]; then
        cp "$source_file" "$target_file"
        print_success "Copied $component/.env.$environment to $component/.env"
    else
        print_error "Template file not found: $source_file"
        return 1
    fi
}

# Function to setup environment
setup_environment() {
    local environment=$1
    
    print_info "Setting up $environment environment..."
    
    # Copy backend environment
    copy_env_template "backend" "$environment"
    
    # Copy frontend environment
    copy_env_template "frontend" "$environment"
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/backend/uploads"
    mkdir -p "$PROJECT_ROOT/backend/data"
    mkdir -p "$PROJECT_ROOT/backend/logs"
    mkdir -p "$PROJECT_ROOT/frontend/dist"
    
    print_success "Environment setup complete for $environment"
}

# Function to validate environment
validate_environment() {
    print_info "Validating environment configuration..."
    
    if [[ -f "$PROJECT_ROOT/scripts/validate_environments.py" ]]; then
        python3 "$PROJECT_ROOT/scripts/validate_environments.py"
    else
        print_warning "Validation script not found. Skipping validation."
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [ENVIRONMENT]"
    echo ""
    echo "Environments:"
    echo "  development  - Setup development environment"
    echo "  staging      - Setup staging environment"
    echo "  production   - Setup production environment"
    echo "  validate     - Validate current environment configuration"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 staging"
    echo "  $0 validate"
}

# Function to interactive setup
interactive_setup() {
    echo ""
    echo "Select environment to setup:"
    echo "1) Development"
    echo "2) Staging"
    echo "3) Production"
    echo "4) Validate current configuration"
    echo "5) Exit"
    
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            setup_environment "development"
            ;;
        2)
            setup_environment "staging"
            print_warning "Remember to replace secret placeholders with actual values!"
            ;;
        3)
            setup_environment "production"
            print_warning "Remember to replace secret placeholders with actual values!"
            print_warning "Ensure all secrets are properly configured in your secret manager!"
            ;;
        4)
            validate_environment
            ;;
        5)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please select 1-5."
            interactive_setup
            ;;
    esac
}

# Main logic
if [[ $# -eq 0 ]]; then
    # No arguments, run interactive setup
    interactive_setup
elif [[ $1 == "help" ]] || [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
    show_help
elif [[ $1 == "validate" ]]; then
    validate_environment
elif [[ $1 == "development" ]] || [[ $1 == "staging" ]] || [[ $1 == "production" ]]; then
    setup_environment "$1"
    
    # Show warnings for non-development environments
    if [[ $1 != "development" ]]; then
        echo ""
        print_warning "IMPORTANT: This is a $1 environment setup!"
        print_warning "Make sure to:"
        print_warning "1. Replace all \${SECRET_NAME} placeholders with actual values"
        print_warning "2. Use a proper secret management system"
        print_warning "3. Validate the configuration before deployment"
        echo ""
        print_info "Run '$0 validate' to check your configuration"
    fi
else
    print_error "Unknown environment: $1"
    show_help
    exit 1
fi

print_success "Environment setup completed!"
