#!/bin/bash

# IPTV Player Restore Script
if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup-file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -1 backups/*.tar.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"
echo "Warning: This will overwrite current files (data directory preserved)"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    tar -xzf "$BACKUP_FILE"
    echo "✓ Restore complete"
    echo ""
    echo "Run 'docker-compose up --build -d' to start"
else
    echo "Restore cancelled"
fi
