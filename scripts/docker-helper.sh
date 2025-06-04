#!/bin/bash

# AskRAG Docker Development Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    print_success "docker-compose is available"
}

# Function to start development environment
start_dev() {
    print_status "Starting AskRAG development environment..."
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.docker.dev .env
        print_success "Created .env file from .env.docker.dev"
    fi
    
    # Build and start services
    docker-compose -f docker-compose.dev.yml up --build -d
    
    print_success "Development environment started!"
    print_status "Services available at:"
    echo "  - Frontend: http://localhost:5173"
    echo "  - Backend API: http://localhost:8000"
    echo "  - MongoDB: localhost:27017"
    echo "  - Redis: localhost:6379"
}

# Function to start production environment
start_prod() {
    print_status "Starting AskRAG production environment..."
    
    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.docker .env
        print_warning "Created .env file from .env.docker - please configure it!"
    fi
    
    # Build and start services
    docker-compose up --build -d
    
    print_success "Production environment started!"
    print_status "Services available at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - MongoDB: localhost:27017"
    echo "  - Redis: localhost:6379"
}

# Function to stop all services
stop_all() {
    print_status "Stopping all AskRAG services..."
    
    docker-compose -f docker-compose.dev.yml down
    docker-compose down
    
    print_success "All services stopped"
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        docker-compose -f docker-compose.dev.yml logs -f
    else
        print_status "Showing logs for service: $service"
        docker-compose -f docker-compose.dev.yml logs -f "$service"
    fi
}

# Function to reset all data
reset_data() {
    print_warning "This will remove all Docker volumes and data. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Stopping services and removing volumes..."
        
        docker-compose -f docker-compose.dev.yml down -v
        docker-compose down -v
        
        # Remove volumes
        docker volume rm askrag_mongodb_data askrag_mongodb_dev_data askrag_redis_data 2>/dev/null || true
        
        print_success "All data reset successfully"
    else
        print_status "Reset cancelled"
    fi
}

# Function to run backend tests
run_tests() {
    print_status "Running backend tests..."
    
    docker-compose -f docker-compose.dev.yml exec backend-dev pytest tests/ -v
    
    print_success "Tests completed"
}

# Function to show service status
show_status() {
    print_status "AskRAG Services Status:"
    docker-compose -f docker-compose.dev.yml ps
}

# Function to open shell in service
shell() {
    local service=${1:-"backend-dev"}
    
    print_status "Opening shell in service: $service"
    docker-compose -f docker-compose.dev.yml exec "$service" /bin/bash
}

# Main script logic
case "${1:-}" in
    "dev"|"start-dev")
        check_docker
        check_docker_compose
        start_dev
        ;;
    "prod"|"start-prod")
        check_docker
        check_docker_compose
        start_prod
        ;;
    "stop")
        stop_all
        ;;
    "logs")
        show_logs "${2:-}"
        ;;
    "status")
        show_status
        ;;
    "reset")
        reset_data
        ;;
    "test")
        run_tests
        ;;
    "shell")
        shell "${2:-}"
        ;;
    *)
        echo "AskRAG Docker Helper Script"
        echo "Usage: $0 {dev|prod|stop|logs|status|reset|test|shell} [service]"
        echo ""
        echo "Commands:"
        echo "  dev        Start development environment"
        echo "  prod       Start production environment"
        echo "  stop       Stop all services"
        echo "  logs       Show logs (optional: specify service)"
        echo "  status     Show service status"
        echo "  reset      Reset all data (removes volumes)"
        echo "  test       Run backend tests"
        echo "  shell      Open shell in service (default: backend-dev)"
        echo ""
        echo "Examples:"
        echo "  $0 dev                 # Start development environment"
        echo "  $0 logs backend-dev    # Show backend logs"
        echo "  $0 shell frontend-dev  # Open shell in frontend container"
        exit 1
        ;;
esac
