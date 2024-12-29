#!/bin/bash

# Set error handling
set -e

echo "Starting system initialization..."

# Script locations
DB_SCRIPTS="./scripts/db"
STORAGE_SCRIPTS="./scripts/storage"
BACKUP_SCRIPTS="./scripts/backup"
UTILS_SCRIPTS="./scripts/utils"

# Clean up and prepare directories
echo "Preparing directories..."
rm -rf ./ddbs_1_data ./ddbs_2_data ./dfs_1_data ./dfs_2_data
rm -f db-generation/articles/mapping_results.txt

mkdir -p ./ddbs_1_data ./ddbs_2_data ./dfs_1_data ./dfs_2_data

# Stop any running containers and remove volumes
echo "Stopping existing containers..."
docker-compose down -v

# Start services
echo "Starting docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 5

# Clear databases and storage
echo "Clearing existing data..."
bash "$DB_SCRIPTS/mongo_drop.sh"
bash "$STORAGE_SCRIPTS/clear_storage.sh"

# Load initial data
echo "Loading initial data..."
python3 bulk_load_data.py
sleep 5
python3 post_bulk_load_data.py

# Generate additional data
echo "Generating additional data..."
docker exec -it python-app bash -c "cd /usr/src/app/ && python3 ./generate_beread.py"
docker exec -it python-app bash -c "cd /usr/src/app/ && python3 ./generate_popular_rank.py"

# Set up and load files
echo "Setting up file storage..."
docker cp "$STORAGE_SCRIPTS/bulk_load_file.sh" storage0:/etc/fdfs_buffer/

echo "Loading files into storage..."
docker exec -it storage0 bash -c "cd /etc/fdfs_buffer/ && bash ./bulk_load_file.sh"

# Update file paths
echo "Updating file paths..."
mv db-generation/articles/mapping_results.txt backend/mapping_results.txt
python3 ./update_file_path.py

echo "Initialization completed successfully at $(date)"
