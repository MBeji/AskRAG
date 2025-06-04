#!/bin/bash
set -euo pipefail

# AskRAG Disaster Recovery Script
# Usage: ./disaster-recovery.sh <environment> <backup_file> [restore_type]

ENVIRONMENT=${1:-production}
BACKUP_FILE=${2:-}
RESTORE_TYPE=${3:-full}  # full, data-only, config-only
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR=$(mktemp -d)

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

# Cleanup function
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Validate inputs
validate_inputs() {
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Backup file not specified"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file does not exist: $BACKUP_FILE"
        exit 1
    fi
    
    case $ENVIRONMENT in
        staging|production)
            log_info "Restoring to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    case $RESTORE_TYPE in
        full|data-only|config-only)
            log_info "Restore type: $RESTORE_TYPE"
            ;;
        *)
            log_error "Invalid restore type: $RESTORE_TYPE"
            exit 1
            ;;
    esac
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."
    
    local checksum_file="${BACKUP_FILE}.sha256"
    
    if [ -f "$checksum_file" ]; then
        if sha256sum -c "$checksum_file"; then
            log_success "Backup integrity verified"
        else
            log_error "Backup integrity check failed"
            exit 1
        fi
    else
        log_warning "No checksum file found, skipping integrity check"
    fi
}

# Extract backup
extract_backup() {
    log_info "Extracting backup..."
    
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    
    # Find the extracted directory
    BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "20*" | head -n1)
    
    if [ -z "$BACKUP_DIR" ]; then
        log_error "Could not find backup directory in archive"
        exit 1
    fi
    
    log_success "Backup extracted to: $BACKUP_DIR"
}

# Read backup metadata
read_backup_metadata() {
    log_info "Reading backup metadata..."
    
    local metadata_file="$BACKUP_DIR/backup-metadata.json"
    
    if [ -f "$metadata_file" ]; then
        log_info "Backup metadata:"
        cat "$metadata_file" | jq '.'
        
        # Verify environment compatibility
        local backup_env=$(cat "$metadata_file" | jq -r '.environment')
        if [ "$backup_env" != "$ENVIRONMENT" ]; then
            log_warning "Backup was created for $backup_env environment, restoring to $ENVIRONMENT"
            read -p "Continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_warning "No metadata file found in backup"
    fi
}

# Scale down applications
scale_down_applications() {
    log_info "Scaling down applications..."
    
    kubectl scale deployment askrag-backend --replicas=0 -n "askrag-$ENVIRONMENT"
    kubectl scale deployment askrag-frontend --replicas=0 -n "askrag-$ENVIRONMENT"
    
    # Wait for pods to terminate
    kubectl wait --for=delete pod -l app=askrag-backend -n "askrag-$ENVIRONMENT" --timeout=300s
    kubectl wait --for=delete pod -l app=askrag-frontend -n "askrag-$ENVIRONMENT" --timeout=300s
    
    log_success "Applications scaled down"
}

# Restore MongoDB data
restore_mongodb() {
    log_info "Restoring MongoDB data..."
    
    local mongo_backup="$BACKUP_DIR/mongodb/mongodb-*.tar.gz"
    
    if [ ! -f $mongo_backup ]; then
        log_warning "No MongoDB backup found"
        return 0
    fi
    
    # Extract MongoDB backup
    local mongo_temp="$TEMP_DIR/mongodb"
    mkdir -p "$mongo_temp"
    tar -xzf $mongo_backup -C "$mongo_temp"
    
    # Get MongoDB pod
    local mongo_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=mongodb \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$mongo_pod" ]; then
        log_error "MongoDB pod not found"
        return 1
    fi
    
    # Get MongoDB credentials
    local mongo_user=$(kubectl get secret askrag-secrets -n "askrag-$ENVIRONMENT" \
        -o jsonpath='{.data.MONGODB_USERNAME}' | base64 -d)
    local mongo_pass=$(kubectl get secret askrag-secrets -n "askrag-$ENVIRONMENT" \
        -o jsonpath='{.data.MONGODB_PASSWORD}' | base64 -d)
    
    # Copy backup to pod
    kubectl cp "$mongo_temp/backup" "askrag-$ENVIRONMENT/$mongo_pod:/tmp/"
    
    # Restore database
    kubectl exec "$mongo_pod" -n "askrag-$ENVIRONMENT" -- \
        mongorestore --username "$mongo_user" --password "$mongo_pass" \
        --authenticationDatabase admin --drop /tmp/backup
    
    log_success "MongoDB data restored"
}

# Restore Redis data
restore_redis() {
    log_info "Restoring Redis data..."
    
    local redis_backup="$BACKUP_DIR/redis/redis-*.rdb"
    
    if [ ! -f $redis_backup ]; then
        log_warning "No Redis backup found"
        return 0
    fi
    
    # Get Redis pod
    local redis_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=redis \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$redis_pod" ]; then
        log_error "Redis pod not found"
        return 1
    fi
    
    # Stop Redis temporarily
    kubectl exec "$redis_pod" -n "askrag-$ENVIRONMENT" -- redis-cli SHUTDOWN NOSAVE || true
    
    # Copy backup to pod
    kubectl cp "$redis_backup" "askrag-$ENVIRONMENT/$redis_pod:/data/dump.rdb"
    
    # Restart Redis pod
    kubectl delete pod "$redis_pod" -n "askrag-$ENVIRONMENT"
    kubectl wait --for=condition=ready pod -l app=redis -n "askrag-$ENVIRONMENT" --timeout=300s
    
    log_success "Redis data restored"
}

# Restore uploaded files
restore_uploads() {
    log_info "Restoring uploaded files..."
    
    local uploads_backup="$BACKUP_DIR/uploads/uploads-*.tar.gz"
    
    if [ ! -f $uploads_backup ]; then
        log_warning "No uploads backup found"
        return 0
    fi
    
    # Get backend pod (we'll need to wait for it to be running)
    kubectl scale deployment askrag-backend --replicas=1 -n "askrag-$ENVIRONMENT"
    kubectl wait --for=condition=ready pod -l app=askrag-backend -n "askrag-$ENVIRONMENT" --timeout=300s
    
    local backend_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=askrag-backend \
        -o jsonpath='{.items[0].metadata.name}')
    
    # Copy and extract uploads
    kubectl cp "$uploads_backup" "askrag-$ENVIRONMENT/$backend_pod:/tmp/uploads-backup.tar.gz"
    kubectl exec "$backend_pod" -n "askrag-$ENVIRONMENT" -- \
        bash -c "rm -rf /app/uploads/* && tar -xzf /tmp/uploads-backup.tar.gz -C /app/uploads/"
    
    log_success "Uploaded files restored"
}

# Restore FAISS index data
restore_faiss_data() {
    log_info "Restoring FAISS index data..."
    
    local faiss_backup="$BACKUP_DIR/uploads/faiss-*.tar.gz"
    
    if [ ! -f $faiss_backup ]; then
        log_warning "No FAISS data backup found"
        return 0
    fi
    
    # Get backend pod
    local backend_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=askrag-backend \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$backend_pod" ]; then
        log_error "Backend pod not found"
        return 1
    fi
    
    # Copy and extract FAISS data
    kubectl cp "$faiss_backup" "askrag-$ENVIRONMENT/$backend_pod:/tmp/faiss-backup.tar.gz"
    kubectl exec "$backend_pod" -n "askrag-$ENVIRONMENT" -- \
        bash -c "rm -rf /app/data/* && tar -xzf /tmp/faiss-backup.tar.gz -C /app/data/"
    
    log_success "FAISS index data restored"
}

# Restore configurations
restore_configs() {
    log_info "Restoring configurations..."
    
    # Restore secrets (carefully, excluding sensitive data)
    local secrets_backup="$BACKUP_DIR/configs/secrets-*.yaml"
    if [ -f $secrets_backup ]; then
        log_warning "Manual review of secrets restore recommended"
        # kubectl apply -f "$secrets_backup"
    fi
    
    # Restore configmaps
    local configmaps_backup="$BACKUP_DIR/configs/configmaps-*.yaml"
    if [ -f $configmaps_backup ]; then
        kubectl apply -f "$configmaps_backup"
        log_success "ConfigMaps restored"
    fi
    
    log_success "Configurations restored"
}

# Scale up applications
scale_up_applications() {
    log_info "Scaling up applications..."
    
    # Get original replica counts from HPA or use defaults
    local backend_replicas=$(kubectl get hpa askrag-backend-hpa -n "askrag-$ENVIRONMENT" \
        -o jsonpath='{.spec.minReplicas}' 2>/dev/null || echo "3")
    local frontend_replicas=$(kubectl get hpa askrag-frontend-hpa -n "askrag-$ENVIRONMENT" \
        -o jsonpath='{.spec.minReplicas}' 2>/dev/null || echo "2")
    
    kubectl scale deployment askrag-backend --replicas="$backend_replicas" -n "askrag-$ENVIRONMENT"
    kubectl scale deployment askrag-frontend --replicas="$frontend_replicas" -n "askrag-$ENVIRONMENT"
    
    # Wait for deployments to be ready
    kubectl rollout status deployment/askrag-backend -n "askrag-$ENVIRONMENT" --timeout=600s
    kubectl rollout status deployment/askrag-frontend -n "askrag-$ENVIRONMENT" --timeout=600s
    
    log_success "Applications scaled up"
}

# Verify restoration
verify_restoration() {
    log_info "Verifying restoration..."
    
    # Run health checks
    local backend_url="http://askrag-backend.askrag-$ENVIRONMENT.svc.cluster.local:8000"
    
    kubectl run restore-verification --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        --timeout=60s \
        -n "askrag-$ENVIRONMENT" \
        -- curl -f "$backend_url/health" && \
    log_success "Backend health check passed" || \
    log_error "Backend health check failed"
    
    # Check database connectivity
    local mongo_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=mongodb \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$mongo_pod" ]; then
        kubectl exec "$mongo_pod" -n "askrag-$ENVIRONMENT" -- \
            mongosh --eval "db.adminCommand('ping')" > /dev/null && \
        log_success "MongoDB connectivity verified" || \
        log_error "MongoDB connectivity failed"
    fi
    
    log_success "Restoration verification completed"
}

# Generate restoration report
generate_restoration_report() {
    log_info "Generating restoration report..."
    
    local report_file="disaster-recovery-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "AskRAG Disaster Recovery Report"
        echo "Environment: $ENVIRONMENT"
        echo "Backup File: $BACKUP_FILE"
        echo "Restore Type: $RESTORE_TYPE"
        echo "Timestamp: $(date)"
        echo "=========================================="
        echo
        
        echo "Restored Components:"
        [ "$RESTORE_TYPE" = "full" ] || [ "$RESTORE_TYPE" = "data-only" ] && echo "- MongoDB data"
        [ "$RESTORE_TYPE" = "full" ] || [ "$RESTORE_TYPE" = "data-only" ] && echo "- Redis data"
        [ "$RESTORE_TYPE" = "full" ] || [ "$RESTORE_TYPE" = "data-only" ] && echo "- Uploaded files"
        [ "$RESTORE_TYPE" = "full" ] || [ "$RESTORE_TYPE" = "data-only" ] && echo "- FAISS index data"
        [ "$RESTORE_TYPE" = "full" ] || [ "$RESTORE_TYPE" = "config-only" ] && echo "- Configurations"
        echo
        
        echo "Current System Status:"
        kubectl get pods -n "askrag-$ENVIRONMENT"
        echo
        
        echo "Services Status:"
        kubectl get services -n "askrag-$ENVIRONMENT"
        echo
        
        echo "RESTORATION COMPLETED SUCCESSFULLY"
        
    } > "$report_file"
    
    log_info "Restoration report saved to: $report_file"
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"AskRAG Disaster Recovery $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Main restoration process
main() {
    log_info "Starting AskRAG disaster recovery process"
    log_info "Environment: $ENVIRONMENT"
    log_info "Backup file: $BACKUP_FILE"
    log_info "Restore type: $RESTORE_TYPE"
    
    # Warning for production
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warning "This will restore to PRODUCTION environment!"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    validate_inputs
    verify_backup
    extract_backup
    read_backup_metadata
    
    case $RESTORE_TYPE in
        full)
            scale_down_applications
            restore_mongodb
            restore_redis
            restore_uploads
            restore_faiss_data
            restore_configs
            scale_up_applications
            ;;
        data-only)
            scale_down_applications
            restore_mongodb
            restore_redis
            restore_uploads
            restore_faiss_data
            scale_up_applications
            ;;
        config-only)
            restore_configs
            ;;
    esac
    
    verify_restoration
    generate_restoration_report
    
    local success_message="Disaster recovery completed successfully for $ENVIRONMENT environment"
    log_success "$success_message"
    send_notification "SUCCESS" "$success_message"
}

# Error handling
handle_error() {
    local exit_code=$?
    local error_message="Disaster recovery failed for $ENVIRONMENT environment at step: ${BASH_COMMAND}"
    
    log_error "$error_message"
    send_notification "FAILED" "$error_message"
    
    exit $exit_code
}

# Set error trap
trap handle_error ERR

# Run main function
main "$@"
