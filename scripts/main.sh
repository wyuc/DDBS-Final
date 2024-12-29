#!/bin/bash

# Set error handling
set -e

# Script locations
DB_SCRIPTS="./scripts/db"
STORAGE_SCRIPTS="./scripts/storage"
BACKUP_SCRIPTS="./scripts/backup"
UTILS_SCRIPTS="./scripts/utils"

# Function to display usage
show_usage() {
    echo "Usage: $0 <command>"
    echo "Commands:"
    echo "  init        - Initialize the entire system"
    echo "  backup      - Backup all databases"
    echo "  restore     - Restore from backup"
    echo "  clear       - Clear all data"
    echo "  help        - Show this help message"
}

# Function to initialize the system
init_system() {
    bash initialization.sh
}

# Function to backup the system
backup_system() {
    echo "Starting backup process..."
    bash "$BACKUP_SCRIPTS/backup_all.sh"
}

# Function to restore the system
restore_system() {
    echo "Starting restore process..."
    bash "$BACKUP_SCRIPTS/restore_all.sh"
}

# Function to clear the system
clear_system() {
    echo "Clearing all data..."
    bash "$DB_SCRIPTS/mongo_drop.sh"
    bash "$STORAGE_SCRIPTS/clear_storage.sh"
}

# Main script logic
case "$1" in
    "init")
        init_system
        ;;
    "backup")
        backup_system
        ;;
    "restore")
        restore_system
        ;;
    "clear")
        clear_system
        ;;
    "help"|"")
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac 