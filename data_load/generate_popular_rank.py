from pymongo import MongoClient
from datetime import datetime
from bson.son import SON

# MongoDB client configuration
clients = [
    [
        MongoClient(host="ddbs_mongo_1", port=27017),
        MongoClient(host="ddbs_mongo_2", port=27017),
    ],
    [
        MongoClient(host="ddbs_mongo_1_bak", port=27017),
        MongoClient(host="ddbs_mongo_2_bak", port=27017),
    ]
]

def get_daily_top_articles(client):
    """
    Aggregates daily top 5 articles based on access count.
    Returns sorted list of results by timestamp.
    """
    pipeline = [
        # Convert timestamp strings to dates
        {'$unwind': '$timestamp'},
        {
            '$addFields': {
                'timestampDate': {
                    '$dateFromString': {'dateString': '$timestamp'}
                }
            }
        },
        # Extract year and day
        {
            '$project': {
                'year': {'$year': '$timestampDate'},
                'day': {'$dayOfYear': '$timestampDate'},
                'aid': '$aid'
            }
        },
        # Group and count accesses
        {
            '$group': {
                '_id': {
                    'year': '$year',
                    'day': '$day',
                    'aid': '$aid'
                },
                'accessCount': {'$sum': 1}
            }
        },
        # Sort by year, day, and access count
        {
            '$sort': {
                '_id.year': 1,
                '_id.day': 1,
                'accessCount': -1
            }
        },
        # Group articles by day
        {
            '$group': {
                '_id': {
                    'year': '$_id.year',
                    'day': '$_id.day'
                },
                'articles': {
                    '$push': {
                        'aid': '$_id.aid',
                        'accessCount': '$accessCount'
                    }
                }
            }
        },
        # Take top 5 articles
        {
            '$project': {
                'articles': {'$slice': ['$articles', 5]},
                'year': '$_id.year',
                'dayOfYear': '$_id.day'
            }
        },
        # Convert to proper date
        {
            '$addFields': {
                'date': {
                    '$function': {
                        'body': 'function(year, dayOfYear) { return new Date(Date.UTC(year, 0, dayOfYear)); }',
                        'args': ['$year', '$dayOfYear'],
                        'lang': 'js'
                    }
                }
            }
        },
        # Final projection
        {
            '$project': {
                'timestamp': {'$toLong': '$date'},
                'temporalGranularity': 'daily',
                'articleAidList': '$articles.aid'
            }
        }
    ]
    results = client.aggregate(pipeline, allowDiskUse=True)
    return sorted(list(results), key=lambda x: x["timestamp"])

def get_weekly_top_articles(client):
    """
    Aggregates weekly top 5 articles based on access count.
    Returns sorted list of results by timestamp.
    """
    pipeline = [
        {'$unwind': '$timestamp'},
        {
            '$addFields': {
                'timestampDate': {
                    '$dateFromString': {'dateString': '$timestamp'}
                }
            }
        },
        # Calculate first day of week
        {
            '$addFields': {
                'firstDayOfWeek': {
                    '$subtract': [
                        '$timestampDate',
                        {
                            '$multiply': [
                                {'$subtract': [{'$dayOfWeek': '$timestampDate'}, 1]},
                                86400000
                            ]
                        }
                    ]
                }
            }
        },
        {
            '$project': {
                'year': {'$year': '$firstDayOfWeek'},
                'day': {'$dayOfYear': '$firstDayOfWeek'},
                'aid': '$aid'
            }
        },
        # Rest of pipeline similar to daily
        {
            '$group': {
                '_id': {
                    'year': '$year',
                    'day': '$day',
                    'aid': '$aid'
                },
                'accessCount': {'$sum': 1}
            }
        },
        {'$sort': {'_id.year': 1, '_id.day': 1, 'accessCount': -1}},
        {
            '$group': {
                '_id': {'year': '$_id.year', 'day': '$_id.day'},
                'articles': {
                    '$push': {
                        'aid': '$_id.aid',
                        'accessCount': '$accessCount'
                    }
                }
            }
        },
        {
            '$project': {
                'articles': {'$slice': ['$articles', 5]},
                'year': '$_id.year',
                'dayOfYear': '$_id.day'
            }
        },
        {
            '$addFields': {
                'date': {
                    '$function': {
                        'body': 'function(year, dayOfYear) { return new Date(Date.UTC(year, 0, dayOfYear)); }',
                        'args': ['$year', '$dayOfYear'],
                        'lang': 'js'
                    }
                }
            }
        },
        {
            '$project': {
                'timestamp': {'$toLong': '$date'},
                'temporalGranularity': 'weekly',
                'articleAidList': '$articles.aid'
            }
        }
    ]
    results = client.aggregate(pipeline)
    return sorted(list(results), key=lambda x: x["timestamp"])

def get_monthly_top_articles(client):
    """
    Aggregates monthly top 5 articles based on access count.
    Returns sorted list of results by timestamp.
    """
    pipeline = [
        {'$unwind': '$timestamp'},
        {
            '$addFields': {
                'timestampDate': {
                    '$dateFromString': {'dateString': '$timestamp'}
                }
            }
        },
        {
            '$project': {
                'year': {'$year': '$timestampDate'},
                'month': {'$month': '$timestampDate'},
                'aid': '$aid'
            }
        },
        {
            '$group': {
                '_id': {
                    'year': '$year',
                    'month': '$month',
                    'aid': '$aid'
                },
                'accessCount': {'$sum': 1}
            }
        },
        {'$sort': {'_id.year': 1, '_id.month': 1, 'accessCount': -1}},
        {
            '$group': {
                '_id': {'year': '$_id.year', 'month': '$_id.month'},
                'articles': {
                    '$push': {
                        'aid': '$_id.aid',
                        'accessCount': '$accessCount'
                    }
                }
            }
        },
        {
            '$project': {
                'articles': {'$slice': ['$articles', 5]},
                'year': '$_id.year',
                'month': '$_id.month'
            }
        },
        {
            '$addFields': {
                'date': {
                    '$dateFromParts': {
                        'year': '$year',
                        'month': '$month'
                    }
                }
            }
        },
        {
            '$project': {
                'timestamp': {'$toLong': '$date'},
                'temporalGranularity': 'monthly',
                'articleAidList': '$articles.aid'
            }
        }
    ]
    results = client.aggregate(pipeline)
    return sorted(list(results), key=lambda x: x["timestamp"])

def main():
    """
    Main execution function that processes and stores top articles
    for daily, weekly, and monthly granularities.
    """
    for db1_client, db2_client in clients:
        top_articles = []
        
        # Aggregate articles for all temporal granularities
        top_articles.extend(get_daily_top_articles(db2_client.history.beread))
        top_articles.extend(get_weekly_top_articles(db2_client.history.beread))
        top_articles.extend(get_monthly_top_articles(db2_client.history.beread))

        # Process and store results
        for _id, article in enumerate(top_articles):
            article["id"] = _id
            del article["_id"]
            
            # Store daily rankings in db1, weekly/monthly in db2
            target_db = db1_client if article["temporalGranularity"] == "daily" else db2_client
            target_db.history.popular_rank.update_one(
                {"timestamp": article["timestamp"]},
                {"$set": article},
                upsert=True
            )

if __name__ == "__main__":
    main()
