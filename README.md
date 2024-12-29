# DDBS Project Manual

## Table of Contents
- [Setup](#setup)
- [Directory Structure](#directory-structure)
- [Scripts](#scripts)
- [Usage](#usage)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.x
- MongoDB
- FastDFS

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd DDBS-Final

# Initialize the system
./scripts/main.sh init
```

## Directory Structure
```
.
├── app/                  # Application code
├── backend/             # Backend services
├── configs/             # Configuration files
├── data_load/           # Data loading scripts
├── db-generation/       # Database generation tools
├── docker/             # Docker configuration
├── scripts/            # Management scripts
│   ├── main.sh         # Main entry point
│   ├── db/            # Database scripts
│   ├── storage/       # Storage scripts
│   ├── backup/        # Backup scripts
│   └── utils/         # Utility scripts
└── initialization.sh   # System initialization
```

## Scripts

### Main Operations
- `./scripts/main.sh init` - Initialize the entire system
- `./scripts/main.sh backup` - Create a system backup
- `./scripts/main.sh restore` - Restore from backup
- `./scripts/main.sh clear` - Clear all data
- `./scripts/main.sh help` - Show help message

### Database Scripts
Located in `scripts/db/`:
- `mongo_drop.sh` - Drop MongoDB databases
- `mongo_dump.sh` - Dump MongoDB databases
- `mongo_restore.sh` - Restore MongoDB databases
- `clear_ddbs1.sh` - Clear DDBS1 instance
- `clear_ddbs1_bak.sh` - Clear DDBS1 backup

### Storage Scripts
Located in `scripts/storage/`:
- `bulk_load_file.sh` - Load files into FastDFS
- `clear_storage.sh` - Clear FastDFS storage

### Backup Scripts
Located in `scripts/backup/`:
- `backup_all.sh` - Complete system backup
- `restore_all.sh` - Complete system restore
- `backup_ddbs1.sh` - Backup DDBS1 instance
- `restore_in_ddbs_1.sh` - Restore DDBS1 instance
- `fuse_ddbs1_from_bak.sh` - Fuse DDBS1 from backup

## Usage

### System Initialization
```bash
./scripts/main.sh init
```
This will:
1. Clean up existing data
2. Start Docker services
3. Initialize databases
4. Load initial data
5. Generate additional data
6. Set up file storage

### Creating Backups
```bash
./scripts/main.sh backup
```
Backups are stored in `/data_load/backups/` with timestamp-based directories.

### Restoring from Backup
```bash
./scripts/main.sh restore [timestamp]
```
If no timestamp is provided, you'll be prompted to select from available backups.

### Clearing Data
```bash
./scripts/main.sh clear
```
This will clear all databases and storage without removing container configurations.

## Backup and Restore

### Backup Structure
Backups are stored in timestamped directories:
```
/data_load/backups/YYYYMMDD_HHMMSS/
├── mongo1/           # DDBS1 MongoDB backup
├── mongo2/           # DDBS2 MongoDB backup
├── storage0_backup.tar.gz  # Storage0 FastDFS backup
└── storage1_backup.tar.gz  # Storage1 FastDFS backup
```

### Automated Backup
The backup system automatically:
1. Creates timestamped backup directory
2. Dumps MongoDB databases
3. Archives FastDFS storage
4. Copies all data to backup location

### Restore Process
The restore process:
1. Lists available backups if no timestamp provided
2. Validates backup directory existence
3. Restores MongoDB databases
4. Restores FastDFS storage
5. Rebuilds necessary indices

## Troubleshooting

### Common Issues

1. **Docker Services Not Starting**
   ```bash
   # Check docker service status
   docker ps
   # Restart docker services
   docker-compose down && docker-compose up -d
   ```

2. **Database Connection Issues**
   ```bash
   # Check MongoDB status
   docker exec ddbs_mongo_1 mongo --eval "db.stats()"
   ```

3. **Storage Issues**
   ```bash
   # Check FastDFS status
   docker exec storage0 fdfs_monitor /etc/fdfs/client.conf
   ```

### Logs
- Docker logs: `docker logs <container_name>`
- MongoDB logs: Check container logs for ddbs_mongo_1 and ddbs_mongo_2
- FastDFS logs: Check container logs for storage0 and storage1

For additional help or issues, please refer to the project documentation or create an issue in the repository. 