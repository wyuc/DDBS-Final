"""
Bulk data loading script for separating and loading data into MongoDB containers.
Handles user, article, and read data distribution across databases.
"""

import json
import logging
import subprocess
from pathlib import Path
from time import sleep
from typing import Set, Dict, Iterator, Any
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_LOAD_PATH = '/data_load'
DB_GENERATION_PATH = 'db-generation'
OUTPUT_PATHS = {
    'db1': 'ddbs_1_data',
    'db2': 'ddbs_2_data'
}

class JsonlHandler:
    @staticmethod
    def load(file_name: str) -> Iterator[dict]:
        """Load JSONL file with error handling."""
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        stripped_line = line.strip()
                        if stripped_line:
                            yield json.loads(stripped_line)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON at line {line_num}: {e}")
        except FileNotFoundError:
            logger.error(f"File not found: {file_name}")
            raise

    @staticmethod
    def dump(objects: Iterator[Any], file_name: str) -> None:
        """Dump objects to JSONL file with error handling."""
        try:
            with open(file_name, 'w', encoding='utf-8') as out_file:
                for obj in objects:
                    out_file.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    out_file.flush()
        except IOError as e:
            logger.error(f"Error writing to file {file_name}: {e}")
            raise

class DockerHelper:
    @staticmethod
    def get_container_names(prefix: str) -> list[str]:
        """Get Docker container names with specified prefix."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                check=True
            )
            return [name for name in result.stdout.splitlines() if name.startswith(prefix)]
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting container names: {e}")
            return []

class DataDistributor:
    def __init__(self):
        self.db1_user_set: Set[str] = set()
        self.db2_user_set: Set[str] = set()
        self.output_files: Dict = {}
        
    def setup_output_files(self):
        """Initialize output files for both databases."""
        for db_key, path in OUTPUT_PATHS.items():
            Path(path).mkdir(exist_ok=True)
            self.output_files[db_key] = {
                'user': open(f"{path}/user.jsonl", 'w'),
                'article': open(f"{path}/article.jsonl", 'w'),
                'read': open(f"{path}/read.jsonl", 'w')
            }

    def close_files(self):
        """Safely close all output files."""
        for db_files in self.output_files.values():
            for f in db_files.values():
                f.close()

    def distribute_user_data(self):
        """Distribute user data based on region."""
        for record in tqdm(JsonlHandler.load(f"{DB_GENERATION_PATH}/user.dat"), desc="Processing users"):
            region = record.get("region")
            if region == "Beijing":
                self.output_files['db1']['user'].write(json.dumps(record) + "\n")
                self.db1_user_set.add(record["uid"])
            elif region == "Hong Kong":
                self.output_files['db2']['user'].write(json.dumps(record) + "\n")
                self.db2_user_set.add(record["uid"])
            else:
                logger.error(f"Invalid region: {region}")
                continue

    def distribute_article_data(self):
        """Distribute article data based on category."""
        for record in tqdm(JsonlHandler.load(f"{DB_GENERATION_PATH}/article.dat"), desc="Processing articles"):
            category = record.get("category")
            if category == "science":
                for db in ['db1', 'db2']:
                    self.output_files[db]['article'].write(json.dumps(record) + "\n")
            elif category == "technology":
                self.output_files['db2']['article'].write(json.dumps(record) + "\n")
            else:
                logger.error(f"Invalid category: {category}")
                continue

    def distribute_read_data(self):
        """Distribute read data based on user sets."""
        for record in tqdm(JsonlHandler.load(f"{DB_GENERATION_PATH}/read.dat"), desc="Processing reads"):
            uid = record.get("uid")
            if uid in self.db1_user_set:
                self.output_files['db1']['read'].write(json.dumps(record) + "\n")
            elif uid in self.db2_user_set:
                self.output_files['db2']['read'].write(json.dumps(record) + "\n")
            else:
                logger.error(f"Unknown user ID: {uid}")
                continue

class MongoImporter:
    @staticmethod
    def import_data(container_name: str) -> None:
        """Import data into MongoDB container using mongoimport."""
        logger.info(f"Loading data for container: {container_name}")
        
        collections = {
            'user': ('info', 'user'),
            'article': ('info', 'article'),
            'read': ('history', 'read'),
            'mapping': ('file', 'mapping')
        }
        
        for collection, (db_name, coll_name) in collections.items():
            file_name = 'file_map.jsonl' if collection == 'mapping' else f'{collection}.jsonl'
            try:
                subprocess.run([
                    'docker', 'exec', container_name,
                    'mongoimport',
                    f'--db={db_name}',
                    f'--collection={coll_name}',
                    f'{DATA_LOAD_PATH}/{file_name}'
                ], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error importing {collection} to {container_name}: {e}")

def refresh_file_mapping():
    """Update file mapping data for both databases."""
    try:
        with open("backend/mapping_results.txt", 'r') as f:
            mapping = [
                dict(name=line.split(" --> ")[0], path=line.split(" --> ")[1].strip())
                for line in f if line.strip()
            ]
        
        for path in OUTPUT_PATHS.values():
            JsonlHandler.dump(mapping, f"{path}/file_map.jsonl")
    except (FileNotFoundError, IndexError) as e:
        logger.error(f"Error processing mapping file: {e}")
        raise

def main():
    try:
        logger.info("Starting bulk data load process")
        sleep(10)  # Wait for MongoDB containers to be ready
        
        refresh_file_mapping()
        
        distributor = DataDistributor()
        try:
            distributor.setup_output_files()
            distributor.distribute_user_data()
            distributor.distribute_article_data()
            distributor.distribute_read_data()
        finally:
            distributor.close_files()
        
        mongo_containers = sorted(
            DockerHelper.get_container_names(prefix="ddbs_mongo_"),
            key=lambda x: len(x)
        )
        
        # Use ThreadPoolExecutor for parallel data import
        with ThreadPoolExecutor(max_workers=len(mongo_containers)) as executor:
            executor.map(MongoImporter.import_data, mongo_containers)
        
        logger.info("Bulk data load completed successfully")
    
    except Exception as e:
        logger.error(f"Fatal error during bulk load: {e}")
        raise

if __name__ == "__main__":
    main()