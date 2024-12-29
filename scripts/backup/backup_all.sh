#!/bin/bash

# Set error handling
set -e

echo "Starting complete backup process..."

# Source directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SCRIPTS="../db"

# Create backup timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/data_load/backups/$TIMESTAMP"

# Create backup directories
mkdir -p "$BACKUP_DIR"

# Backup MongoDB databases
echo "Backing up MongoDB databases..."
docker exec ddbs_mongo_1 bash -c "cd /scripts/db && ./mongo_dump.sh"
docker exec ddbs_mongo_2 bash -c "cd /scripts/db && ./mongo_dump.sh"

# Backup DDBS instances
echo "Backing up DDBS instances..."
bash "$SCRIPT_DIR/backup_ddbs1.sh"

# Archive FastDFS data
echo "Backing up FastDFS data..."
docker exec storage0 tar czf /tmp/storage0_backup.tar.gz /etc/fdfs_buffer
docker exec storage1 tar czf /tmp/storage1_backup.tar.gz /etc/fdfs_buffer

# Copy backups to backup directory
docker cp ddbs_mongo_1:/data_load/dumps/. "$BACKUP_DIR/mongo1/"
docker cp ddbs_mongo_2:/data_load/dumps/. "$BACKUP_DIR/mongo2/"
docker cp storage0:/tmp/storage0_backup.tar.gz "$BACKUP_DIR/"
docker cp storage1:/tmp/storage1_backup.tar.gz "$BACKUP_DIR/"

echo "Backup completed successfully at $(date)"
echo "Backup stored in: $BACKUP_DIR" 