#!/bin/bash

# Set error handling
set -e

echo "Starting complete restore process..."

# Source directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SCRIPTS="../db"

# Function to list available backups
list_backups() {
    ls -lt /data_load/backups/
}

# Function to select backup
select_backup() {
    if [ -z "$1" ]; then
        echo "Available backups:"
        list_backups
        read -p "Enter backup timestamp to restore: " BACKUP_TIMESTAMP
    else
        BACKUP_TIMESTAMP=$1
    fi
    BACKUP_DIR="/data_load/backups/$BACKUP_TIMESTAMP"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "Error: Backup directory $BACKUP_DIR does not exist"
        exit 1
    fi
}

# Get backup to restore
select_backup "$1"

# Restore MongoDB databases
echo "Restoring MongoDB databases..."
docker cp "$BACKUP_DIR/mongo1/." ddbs_mongo_1:/data_load/dumps/
docker cp "$BACKUP_DIR/mongo2/." ddbs_mongo_2:/data_load/dumps/
docker exec ddbs_mongo_1 bash -c "cd /scripts/db && ./mongo_restore.sh"
docker exec ddbs_mongo_2 bash -c "cd /scripts/db && ./mongo_restore.sh"

# Restore DDBS instances
echo "Restoring DDBS instances..."
bash "$SCRIPT_DIR/restore_in_ddbs_1.sh"

# Restore FastDFS data
echo "Restoring FastDFS data..."
docker cp "$BACKUP_DIR/storage0_backup.tar.gz" storage0:/tmp/
docker cp "$BACKUP_DIR/storage1_backup.tar.gz" storage1:/tmp/
docker exec storage0 tar xzf /tmp/storage0_backup.tar.gz -C /
docker exec storage1 tar xzf /tmp/storage1_backup.tar.gz -C /

echo "Restore completed successfully at $(date)" 