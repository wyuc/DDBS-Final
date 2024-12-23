#!/bin/bash

# Bring down any currently running containers and remove volumes
echo "Stopping and removing all containers and volumes..."
docker-compose down -v

# Clean up all data directories
echo "Cleaning up data directories..."
rm -rf ./ddbs_1_data
rm -rf ./ddbs_2_data
rm -rf ./dfs_1_data
rm -rf ./dfs_2_data
rm -f db-generation/articles/mapping_results.txt

# Recreate clean directories
echo "Creating fresh directories..."
mkdir -p ./ddbs_1_data
mkdir -p ./ddbs_2_data
mkdir -p ./dfs_1_data
mkdir -p ./dfs_2_data

# Start the Docker Compose services in detached mode
echo "Starting docker services..."
docker-compose up -d

# Wait for MongoDB to be ready
sleep 5

# Clear MongoDB databases
echo "Clearing MongoDB databases..."
docker exec ddbs_mongo_1 mongo --eval "db.dropDatabase()"
docker exec ddbs_mongo_2 mongo --eval "db.dropDatabase()"
docker exec ddbs_mongo_1_bak mongo --eval "db.dropDatabase()"
docker exec ddbs_mongo_2_bak mongo --eval "db.dropDatabase()"

# Clear FastDFS storage
echo "Clearing FastDFS storage..."
docker exec storage0 rm -rf /etc/fdfs_buffer/*
docker exec storage1 rm -rf /etc/fdfs_buffer/*

# Run your Python script
python3 bulk_load_data.py
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0
sleep 5;
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0
python3 post_bulk_load_data.py
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0
docker exec -it python-app bash -c "cd /usr/src/app/ && python3 ./generate_beread.py"
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0
docker exec -it python-app bash -c "cd /usr/src/app/ && python3 ./generate_popular_rank.py"
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0

docker cp bulk_load_file.sh storage0:/etc/fdfs_buffer/
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0

echo "Uploading Files"
docker exec -it storage0 bash -c "cd /etc/fdfs_buffer/ && bash ./bulk_load_file.sh"
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0

mv db-generation/articles/mapping_results.txt backend/mapping_results.txt
python3 ./update_file_path.py
echo "Line $LINENO: $(date) - Command took $SECONDS seconds"; SECONDS=0
