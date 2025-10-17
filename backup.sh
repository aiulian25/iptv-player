#!/bin/bash

# IPTV Player Backup Script
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
BACKUP_NAME="iptv-player-backup-${TIMESTAMP}"

echo "Creating backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Create backup
tar -czf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz \
    --exclude='data' \
    --exclude='backups' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    docker-compose.yml \
    Dockerfile \
    nginx.conf \
    backend/ \
    frontend/ \
    README.md 2>/dev/null

echo "✓ Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "To restore this backup:"
echo "  tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "Current data directory preserved at: ./data"
