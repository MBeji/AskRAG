#!/bin/bash
set -euo pipefail

# AskRAG Deployment Validation Script
# Usage: ./validate-deployment.sh <environment>

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Validation results
VALIDATION_PASSED=true

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        staging|production)
            log_info "Validating $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
            exit 1
            ;;
    esac
}

# Check namespace exists
check_namespace() {
    log_info "Checking namespace..."
    if kubectl get namespace "askrag-$ENVIRONMENT" &> /dev/null; then
        log_success "Namespace askrag-$ENVIRONMENT exists"
    else
        log_error "Namespace askrag-$ENVIRONMENT does not exist"
        VALIDATION_PASSED=false
    fi
}

# Check all required pods are running
check_pods() {
    log_info "Checking pod status..."
    
    local required_apps=("mongodb" "redis" "askrag-backend" "askrag-frontend")
    
    for app in "${required_apps[@]}"; do
        local pod_count=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app="$app" \
            --field-selector=status.phase=Running --no-headers | wc -l)
        
        if [ "$pod_count" -gt 0 ]; then
            log_success "$app: $pod_count pod(s) running"
        else
            log_error "$app: No running pods found"
            VALIDATION_PASSED=false
        fi
    done
}

# Check services are accessible
check_services() {
    log_info "Checking services..."
    
    local services=("mongodb" "redis" "askrag-backend" "askrag-frontend")
    
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "askrag-$ENVIRONMENT" &> /dev/null; then
            local endpoints=$(kubectl get endpoints "$service" -n "askrag-$ENVIRONMENT" \
                -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
            
            if [ "$endpoints" -gt 0 ]; then
                log_success "$service: Service active with $endpoints endpoint(s)"
            else
                log_warning "$service: Service exists but no endpoints"
            fi
        else
            log_error "$service: Service not found"
            VALIDATION_PASSED=false
        fi
    done
}

# Check persistent volumes
check_storage() {
    log_info "Checking persistent volumes..."
    
    local pvcs=("mongodb-storage" "redis-storage" "uploads-storage" "faiss-storage" "logs-storage")
    
    for pvc in "${pvcs[@]}"; do
        local status=$(kubectl get pvc "$pvc" -n "askrag-$ENVIRONMENT" \
            -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
        
        if [ "$status" = "Bound" ]; then
            log_success "$pvc: Bound"
        else
            log_error "$pvc: $status"
            VALIDATION_PASSED=false
        fi
    done
}

# Check ingress configuration
check_ingress() {
    log_info "Checking ingress..."
    
    if kubectl get ingress askrag-ingress -n "askrag-$ENVIRONMENT" &> /dev/null; then
        local address=$(kubectl get ingress askrag-ingress -n "askrag-$ENVIRONMENT" \
            -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        
        if [ -n "$address" ]; then
            log_success "Ingress: External IP assigned ($address)"
        else
            log_warning "Ingress: No external IP assigned yet"
        fi
    else
        log_error "Ingress: askrag-ingress not found"
        VALIDATION_PASSED=false
    fi
}

# Check HPA (Horizontal Pod Autoscaler)
check_hpa() {
    log_info "Checking HPA..."
    
    local hpas=("askrag-backend-hpa" "askrag-frontend-hpa")
    
    for hpa in "${hpas[@]}"; do
        if kubectl get hpa "$hpa" -n "askrag-$ENVIRONMENT" &> /dev/null; then
            local current_replicas=$(kubectl get hpa "$hpa" -n "askrag-$ENVIRONMENT" \
                -o jsonpath='{.status.currentReplicas}')
            local desired_replicas=$(kubectl get hpa "$hpa" -n "askrag-$ENVIRONMENT" \
                -o jsonpath='{.status.desiredReplicas}')
            
            log_success "$hpa: $current_replicas/$desired_replicas replicas"
        else
            log_error "$hpa: Not found"
            VALIDATION_PASSED=false
        fi
    done
}

# Perform health checks
check_health_endpoints() {
    log_info "Checking health endpoints..."
    
    # Create a temporary pod for testing
    kubectl run validation-test --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        --timeout=60s \
        -n "askrag-$ENVIRONMENT" \
        --command -- /bin/sh -c "
            echo 'Testing backend health endpoint...'
            if curl -f -s http://askrag-backend:8000/health > /dev/null; then
                echo 'Backend health check: PASSED'
            else
                echo 'Backend health check: FAILED'
                exit 1
            fi
            
            echo 'Testing frontend availability...'
            if curl -f -s http://askrag-frontend:3000/ > /dev/null; then
                echo 'Frontend availability check: PASSED'
            else
                echo 'Frontend availability check: FAILED'
                exit 1
            fi
        " && log_success "Health endpoints: All checks passed" || {
            log_error "Health endpoints: Some checks failed"
            VALIDATION_PASSED=false
        }
}

# Check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Get node resource usage
    kubectl top nodes 2>/dev/null && log_success "Node metrics available" || \
        log_warning "Node metrics not available (metrics-server may not be installed)"
    
    # Get pod resource usage
    kubectl top pods -n "askrag-$ENVIRONMENT" 2>/dev/null && \
        log_success "Pod metrics available" || \
        log_warning "Pod metrics not available"
}

# Check logs for errors
check_logs() {
    log_info "Checking recent logs for errors..."
    
    local apps=("askrag-backend" "askrag-frontend")
    
    for app in "${apps[@]}"; do
        local pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app="$app" \
            -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        
        if [ -n "$pod" ]; then
            local error_count=$(kubectl logs "$pod" -n "askrag-$ENVIRONMENT" \
                --since=5m 2>/dev/null | grep -i -E "error|exception|failed" | wc -l)
            
            if [ "$error_count" -eq 0 ]; then
                log_success "$app: No recent errors in logs"
            else
                log_warning "$app: $error_count error(s) found in recent logs"
            fi
        fi
    done
}

# Generate validation report
generate_report() {
    log_info "Generating validation report..."
    
    local report_file="deployment-validation-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "AskRAG Deployment Validation Report"
        echo "Environment: $ENVIRONMENT"
        echo "Timestamp: $(date)"
        echo "=========================================="
        echo
        
        echo "Namespace Status:"
        kubectl get namespace "askrag-$ENVIRONMENT" 2>/dev/null || echo "Namespace not found"
        echo
        
        echo "Pod Status:"
        kubectl get pods -n "askrag-$ENVIRONMENT" 2>/dev/null || echo "No pods found"
        echo
        
        echo "Service Status:"
        kubectl get services -n "askrag-$ENVIRONMENT" 2>/dev/null || echo "No services found"
        echo
        
        echo "PVC Status:"
        kubectl get pvc -n "askrag-$ENVIRONMENT" 2>/dev/null || echo "No PVCs found"
        echo
        
        echo "Ingress Status:"
        kubectl get ingress -n "askrag-$ENVIRONMENT" 2>/dev/null || echo "No ingress found"
        echo
        
        echo "HPA Status:"
        kubectl get hpa -n "askrag-$ENVIRONMENT" 2>/dev/null || echo "No HPA found"
        echo
        
        if [ "$VALIDATION_PASSED" = true ]; then
            echo "VALIDATION RESULT: PASSED"
        else
            echo "VALIDATION RESULT: FAILED"
        fi
        
    } > "$report_file"
    
    log_info "Validation report saved to: $report_file"
}

# Main validation process
main() {
    log_info "Starting deployment validation for $ENVIRONMENT"
    
    validate_environment
    check_namespace
    check_pods
    check_services
    check_storage
    check_ingress
    check_hpa
    check_health_endpoints
    check_resource_usage
    check_logs
    generate_report
    
    echo
    if [ "$VALIDATION_PASSED" = true ]; then
        log_success "All validation checks passed!"
        exit 0
    else
        log_error "Some validation checks failed!"
        exit 1
    fi
}

# Run main function
main "$@"
