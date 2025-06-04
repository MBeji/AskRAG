#!/bin/bash
set -euo pipefail

# AskRAG Backup Script
# Usage: ./backup.sh <environment> [backup_type]

ENVIRONMENT=${1:-production}
BACKUP_TYPE=${2:-full}  # full, incremental, config-only
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="/backups/askrag"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

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

# Validate inputs
validate_inputs() {
    case $ENVIRONMENT in
        staging|production)
            log_info "Creating backup for $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    case $BACKUP_TYPE in
        full|incremental|config-only)
            log_info "Backup type: $BACKUP_TYPE"
            ;;
        *)
            log_error "Invalid backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac
}

# Create backup directory structure
create_backup_structure() {
    local backup_path="$BACKUP_DIR/$ENVIRONMENT/$TIMESTAMP"
    
    mkdir -p "$backup_path"/{mongodb,redis,uploads,configs,k8s}
    
    export BACKUP_PATH="$backup_path"
    log_success "Backup directory created: $backup_path"
}

# Backup MongoDB data
backup_mongodb() {
    log_info "Backing up MongoDB data..."
    
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
    
    # Create MongoDB dump
    kubectl exec "$mongo_pod" -n "askrag-$ENVIRONMENT" -- \
        mongodump --username "$mongo_user" --password "$mongo_pass" \
        --authenticationDatabase admin --out /tmp/backup
    
    # Copy dump to backup location
    kubectl cp "askrag-$ENVIRONMENT/$mongo_pod:/tmp/backup" \
        "$BACKUP_PATH/mongodb/"
    
    # Compress the backup
    tar -czf "$BACKUP_PATH/mongodb/mongodb-$TIMESTAMP.tar.gz" \
        -C "$BACKUP_PATH/mongodb" backup
    rm -rf "$BACKUP_PATH/mongodb/backup"
    
    log_success "MongoDB backup completed"
}

# Backup Redis data
backup_redis() {
    log_info "Backing up Redis data..."
    
    local redis_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=redis \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$redis_pod" ]; then
        log_error "Redis pod not found"
        return 1
    fi
    
    # Create Redis backup
    kubectl exec "$redis_pod" -n "askrag-$ENVIRONMENT" -- \
        redis-cli BGSAVE
    
    # Wait for background save to complete
    while [ "$(kubectl exec "$redis_pod" -n "askrag-$ENVIRONMENT" -- redis-cli LASTSAVE)" = "$(kubectl exec "$redis_pod" -n "askrag-$ENVIRONMENT" -- redis-cli LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy Redis dump
    kubectl cp "askrag-$ENVIRONMENT/$redis_pod:/data/dump.rdb" \
        "$BACKUP_PATH/redis/redis-$TIMESTAMP.rdb"
    
    log_success "Redis backup completed"
}

# Backup uploaded files
backup_uploads() {
    log_info "Backing up uploaded files..."
    
    local backend_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=askrag-backend \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$backend_pod" ]; then
        log_error "Backend pod not found"
        return 1
    fi
    
    # Create tar archive of uploads
    kubectl exec "$backend_pod" -n "askrag-$ENVIRONMENT" -- \
        tar -czf /tmp/uploads-backup.tar.gz -C /app/uploads .
    
    # Copy uploads backup
    kubectl cp "askrag-$ENVIRONMENT/$backend_pod:/tmp/uploads-backup.tar.gz" \
        "$BACKUP_PATH/uploads/uploads-$TIMESTAMP.tar.gz"
    
    log_success "Uploads backup completed"
}

# Backup FAISS index data
backup_faiss_data() {
    log_info "Backing up FAISS index data..."
    
    local backend_pod=$(kubectl get pods -n "askrag-$ENVIRONMENT" -l app=askrag-backend \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$backend_pod" ]; then
        log_error "Backend pod not found"
        return 1
    fi
    
    # Create tar archive of FAISS data
    kubectl exec "$backend_pod" -n "askrag-$ENVIRONMENT" -- \
        tar -czf /tmp/faiss-backup.tar.gz -C /app/data .
    
    # Copy FAISS backup
    kubectl cp "askrag-$ENVIRONMENT/$backend_pod:/tmp/faiss-backup.tar.gz" \
        "$BACKUP_PATH/uploads/faiss-$TIMESTAMP.tar.gz"
    
    log_success "FAISS data backup completed"
}

# Backup configurations
backup_configs() {
    log_info "Backing up configurations..."
    
    # Backup secrets (excluding sensitive data)
    kubectl get secrets -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/configs/secrets-$TIMESTAMP.yaml"
    
    # Backup configmaps
    kubectl get configmaps -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/configs/configmaps-$TIMESTAMP.yaml"
    
    # Backup PVCs
    kubectl get pvc -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/configs/pvcs-$TIMESTAMP.yaml"
    
    log_success "Configurations backup completed"
}

# Backup Kubernetes manifests
backup_k8s_manifests() {
    log_info "Backing up Kubernetes manifests..."
    
    # Backup all resources in namespace
    kubectl get all,ingress,pvc,secrets,configmaps -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/k8s/all-resources-$TIMESTAMP.yaml"
    
    # Backup specific deployments
    kubectl get deployment -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/k8s/deployments-$TIMESTAMP.yaml"
    
    # Backup services
    kubectl get service -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/k8s/services-$TIMESTAMP.yaml"
    
    # Backup HPA
    kubectl get hpa -n "askrag-$ENVIRONMENT" -o yaml > \
        "$BACKUP_PATH/k8s/hpa-$TIMESTAMP.yaml"
    
    log_success "Kubernetes manifests backup completed"
}

# Create backup metadata
create_backup_metadata() {
    log_info "Creating backup metadata..."
    
    cat > "$BACKUP_PATH/backup-metadata.json" << EOF
{
    "backup_id": "$TIMESTAMP",
    "environment": "$ENVIRONMENT",
    "backup_type": "$BACKUP_TYPE",
    "timestamp": "$(date -Iseconds)",
    "created_by": "${USER:-unknown}",
    "components": {
        "mongodb": $([ -f "$BACKUP_PATH/mongodb/mongodb-$TIMESTAMP.tar.gz" ] && echo "true" || echo "false"),
        "redis": $([ -f "$BACKUP_PATH/redis/redis-$TIMESTAMP.rdb" ] && echo "true" || echo "false"),
        "uploads": $([ -f "$BACKUP_PATH/uploads/uploads-$TIMESTAMP.tar.gz" ] && echo "true" || echo "false"),
        "faiss": $([ -f "$BACKUP_PATH/uploads/faiss-$TIMESTAMP.tar.gz" ] && echo "true" || echo "false"),
        "configs": $([ -f "$BACKUP_PATH/configs/secrets-$TIMESTAMP.yaml" ] && echo "true" || echo "false"),
        "k8s": $([ -f "$BACKUP_PATH/k8s/all-resources-$TIMESTAMP.yaml" ] && echo "true" || echo "false")
    },
    "size_mb": $(du -sm "$BACKUP_PATH" | cut -f1),
    "kubernetes_version": "$(kubectl version --short --client | grep 'Client Version')",
    "backup_script_version": "1.0.0"
}
EOF
    
    log_success "Backup metadata created"
}

# Compress and finalize backup
finalize_backup() {
    log_info "Finalizing backup..."
    
    # Create final compressed archive
    local final_backup="$BACKUP_DIR/$ENVIRONMENT/askrag-$ENVIRONMENT-$BACKUP_TYPE-$TIMESTAMP.tar.gz"
    
    tar -czf "$final_backup" -C "$BACKUP_DIR/$ENVIRONMENT" "$TIMESTAMP"
    
    # Calculate checksums
    sha256sum "$final_backup" > "$final_backup.sha256"
    
    # Remove temporary directory
    rm -rf "$BACKUP_PATH"
    
    log_success "Backup finalized: $final_backup"
    log_info "Backup size: $(du -h "$final_backup" | cut -f1)"
    log_info "Checksum: $(cat "$final_backup.sha256")"
}

# Clean old backups
clean_old_backups() {
    log_info "Cleaning old backups..."
    
    # Keep last 7 daily backups, 4 weekly backups, 12 monthly backups
    find "$BACKUP_DIR/$ENVIRONMENT" -name "askrag-$ENVIRONMENT-*.tar.gz" -mtime +7 -delete
    
    log_success "Old backups cleaned"
}

# Upload to remote storage (if configured)
upload_to_remote() {
    if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
        log_info "Uploading backup to S3..."
        
        local final_backup="$BACKUP_DIR/$ENVIRONMENT/askrag-$ENVIRONMENT-$BACKUP_TYPE-$TIMESTAMP.tar.gz"
        
        aws s3 cp "$final_backup" "s3://$BACKUP_S3_BUCKET/askrag/$ENVIRONMENT/" || {
            log_warning "Failed to upload to S3"
        }
        
        aws s3 cp "$final_backup.sha256" "s3://$BACKUP_S3_BUCKET/askrag/$ENVIRONMENT/" || {
            log_warning "Failed to upload checksum to S3"
        }
        
        log_success "Backup uploaded to S3"
    fi
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"AskRAG Backup $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
    
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$message" | mail -s "AskRAG Backup $status" "$NOTIFICATION_EMAIL" || true
    fi
}

# Main backup process
main() {
    log_info "Starting AskRAG backup process"
    log_info "Environment: $ENVIRONMENT"
    log_info "Backup type: $BACKUP_TYPE"
    log_info "Timestamp: $TIMESTAMP"
    
    validate_inputs
    create_backup_structure
    
    case $BACKUP_TYPE in
        full)
            backup_mongodb
            backup_redis
            backup_uploads
            backup_faiss_data
            backup_configs
            backup_k8s_manifests
            ;;
        incremental)
            backup_mongodb
            backup_uploads
            backup_faiss_data
            ;;
        config-only)
            backup_configs
            backup_k8s_manifests
            ;;
    esac
    
    create_backup_metadata
    finalize_backup
    clean_old_backups
    upload_to_remote
    
    local backup_size=$(du -h "$BACKUP_DIR/$ENVIRONMENT/askrag-$ENVIRONMENT-$BACKUP_TYPE-$TIMESTAMP.tar.gz" | cut -f1)
    local success_message="Backup completed successfully for $ENVIRONMENT environment. Size: $backup_size"
    
    log_success "$success_message"
    send_notification "SUCCESS" "$success_message"
}

# Error handling
handle_error() {
    local exit_code=$?
    local error_message="Backup failed for $ENVIRONMENT environment at step: ${BASH_COMMAND}"
    
    log_error "$error_message"
    send_notification "FAILED" "$error_message"
    
    exit $exit_code
}

# Set error trap
trap handle_error ERR

# Run main function
main "$@"
