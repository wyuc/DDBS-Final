from pymongo import MongoClient
from tqdm import tqdm
import datetime
from typing import List, Dict, Any

def get_mongo_clients() -> List[List[MongoClient]]:
    """Initialize and return MongoDB client connections."""
    return [
        [
            MongoClient(host="ddbs_mongo_1", port=27017),
            MongoClient(host="ddbs_mongo_2", port=27017),
        ],
        [
            MongoClient(host="ddbs_mongo_1_bak", port=27017),
            MongoClient(host="ddbs_mongo_2_bak", port=27017),
        ]
    ]

def create_indexes(clients: List[List[MongoClient]]) -> None:
    """Create necessary indexes on MongoDB collections."""
    for db1_client, db2_client in clients:
        db1_client.history.read.create_index([("aid", 1)])
        db2_client.history.read.create_index([("aid", 1)])

def process_read_records(read_records, beread: Dict[str, Any]) -> None:
    """Process read records and update beread statistics."""
    for read_record in read_records:
        # Convert timestamp to ISO format
        timestamp = datetime.datetime.fromtimestamp(
            int(read_record["timestamp"]) / 1000
        ).isoformat()
        
        # Update basic read statistics
        beread["timestamp"].append(timestamp)
        beread["readNum"] += 1
        beread["readUidList"].append(read_record["uid"])
        
        # Update interaction statistics
        if int(read_record["commentOrNot"]):
            beread["commentNum"] += 1
            beread["commentUidList"].append(read_record["uid"])
        if int(read_record["agreeOrNot"]):
            beread["agreeNum"] += 1
            beread["agreeUidList"].append(read_record["uid"])
        if int(read_record["shareOrNot"]):
            beread["shareNum"] += 1
            beread["shareUidList"].append(read_record["uid"])

def initialize_beread(article: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize beread dictionary with default values."""
    return {
        "id": article["id"],
        "timestamp": list(),
        "aid": article["aid"],
        "readNum": 0,
        "readUidList": list(),
        "commentNum": 0,
        "commentUidList": list(),
        "agreeNum": 0,
        "agreeUidList": list(),
        "shareNum": 0,
        "shareUidList": list(),
    }

def update_beread_collections(db1_client: MongoClient, 
                            db2_client: MongoClient, 
                            beread: Dict[str, Any], 
                            aid: str,
                            category: str) -> None:
    """Update beread collections in MongoDB."""
    # Always update db2
    db2_client.history.beread.update_one(
        {"aid": aid},
        {"$set": beread},
        upsert=True
    )
    
    # Update db1 only for science category
    if category == "science":
        db1_client.history.beread.update_one(
            {"aid": aid},
            {"$set": beread},
            upsert=True
        )

def main():
    """Main function to generate beread data."""
    clients = get_mongo_clients()
    create_indexes(clients)

    for db1_client, db2_client in clients:
        # Process all articles with progress bar
        for article in tqdm(db2_client.info.article.find({}), total=10000):
            aid = article["aid"]
            beread = initialize_beread(article)

            # Process read records from both databases
            process_read_records(db1_client.history.read.find({"aid": aid}), beread)
            process_read_records(db2_client.history.read.find({"aid": aid}), beread)

            # Update beread collections
            update_beread_collections(
                db1_client,
                db2_client,
                beread,
                aid,
                article["category"]
            )

if __name__ == "__main__":
    main()
