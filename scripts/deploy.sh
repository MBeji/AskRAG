#!/bin/bash
set -euo pipefail

# AskRAG Deployment Script
# Usage: ./deploy.sh <environment> <image_tag>

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if kubectl context is set
    if ! kubectl config current-context &> /dev/null; then
        log_error "No kubectl context is set"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "askrag-$ENVIRONMENT" &> /dev/null; then
        log_info "Creating namespace askrag-$ENVIRONMENT"
        kubectl apply -f "$K8S_DIR/namespace.yaml"
    fi
    
    log_success "Prerequisites check passed"
}

# Update image tags in manifests
update_image_tags() {
    log_info "Updating image tags to $IMAGE_TAG..."
    
    # Create temporary directory for modified manifests
    TEMP_DIR=$(mktemp -d)
    cp -r "$K8S_DIR"/* "$TEMP_DIR/"
    
    # Update backend image tag
    sed -i "s|ghcr.io/.*askrag.*backend:.*|ghcr.io/$GITHUB_REPOSITORY/backend:$IMAGE_TAG|g" \
        "$TEMP_DIR/backend.yaml"
    
    # Update frontend image tag
    sed -i "s|ghcr.io/.*askrag.*frontend:.*|ghcr.io/$GITHUB_REPOSITORY/frontend:$IMAGE_TAG|g" \
        "$TEMP_DIR/frontend.yaml"
    
    # Export temp dir for later use
    export MANIFEST_DIR="$TEMP_DIR"
    
    log_success "Image tags updated"
}

# Deploy core infrastructure
deploy_infrastructure() {
    log_info "Deploying core infrastructure..."
    
    # Apply in order
    kubectl apply -f "$MANIFEST_DIR/namespace.yaml"
    kubectl apply -f "$MANIFEST_DIR/secrets.yaml"
    kubectl apply -f "$MANIFEST_DIR/configmap.yaml"
    kubectl apply -f "$MANIFEST_DIR/storage.yaml"
    
    log_success "Core infrastructure deployed"
}

# Deploy databases
deploy_databases() {
    log_info "Deploying databases..."
    
    kubectl apply -f "$MANIFEST_DIR/mongodb.yaml"
    kubectl apply -f "$MANIFEST_DIR/redis.yaml"
    
    # Wait for databases to be ready
    log_info "Waiting for MongoDB to be ready..."
    kubectl wait --for=condition=ready pod -l app=mongodb \
        -n "askrag-$ENVIRONMENT" --timeout=300s
    
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis \
        -n "askrag-$ENVIRONMENT" --timeout=300s
    
    log_success "Databases deployed and ready"
}

# Deploy applications
deploy_applications() {
    log_info "Deploying applications..."
    
    # Deploy backend
    kubectl apply -f "$MANIFEST_DIR/backend.yaml"
    
    # Wait for backend rollout
    log_info "Waiting for backend deployment..."
    kubectl rollout status deployment/askrag-backend \
        -n "askrag-$ENVIRONMENT" --timeout=600s
    
    # Deploy frontend
    kubectl apply -f "$MANIFEST_DIR/frontend.yaml"
    
    # Wait for frontend rollout
    log_info "Waiting for frontend deployment..."
    kubectl rollout status deployment/askrag-frontend \
        -n "askrag-$ENVIRONMENT" --timeout=600s
    
    log_success "Applications deployed"
}

# Deploy ingress
deploy_ingress() {
    log_info "Deploying ingress..."
    
    kubectl apply -f "$MANIFEST_DIR/ingress.yaml"
    
    log_success "Ingress deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check all pods are running
    log_info "Checking pod status..."
    kubectl get pods -n "askrag-$ENVIRONMENT"
    
    # Check services
    log_info "Checking services..."
    kubectl get services -n "askrag-$ENVIRONMENT"
    
    # Check ingress
    log_info "Checking ingress..."
    kubectl get ingress -n "askrag-$ENVIRONMENT"
    
    # Health check
    BACKEND_URL="http://askrag-backend.askrag-$ENVIRONMENT.svc.cluster.local:8000"
    log_info "Performing health check..."
    
    if kubectl run health-check --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        --timeout=60s \
        -n "askrag-$ENVIRONMENT" \
        -- curl -f "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_warning "Health check failed, but deployment may still be starting"
    fi
}

# Cleanup function
cleanup() {
    if [ -n "${MANIFEST_DIR:-}" ] && [ -d "$MANIFEST_DIR" ]; then
        rm -rf "$MANIFEST_DIR"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment process
main() {
    log_info "Starting AskRAG deployment to $ENVIRONMENT"
    log_info "Image tag: $IMAGE_TAG"
    
    validate_environment
    check_prerequisites
    update_image_tags
    deploy_infrastructure
    deploy_databases
    deploy_applications
    deploy_ingress
    verify_deployment
    
    log_success "Deployment to $ENVIRONMENT completed successfully!"
    log_info "Applications should be available shortly at the configured ingress endpoints"
}

# Run main function
main "$@"
