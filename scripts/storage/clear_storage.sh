#!/bin/bash

# Set error handling
set -e

echo "Clearing FastDFS storage..."

# Clear storage0
echo "Clearing storage0..."
docker exec storage0 rm -rf /etc/fdfs_buffer/*

# Clear storage1
echo "Clearing storage1..."
docker exec storage1 rm -rf /etc/fdfs_buffer/*

echo "Storage cleared successfully at $(date)" 