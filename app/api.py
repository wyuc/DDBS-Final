from flask import Flask, request, Response, render_template
import requests
from pymongo import MongoClient
from tqdm import tqdm
from datetime import datetime
clients = dict(
    db1 = [
        MongoClient(host="localhost", port=27001),
        MongoClient(host="localhost", port=27002),
        ],
    db2 = [
        MongoClient(host="localhost", port=27003),
        MongoClient(host="localhost", port=27004),
        ]
    )
app = Flask(__name__)

def convert_file_to_path(file_name):
    for client in sum(list(clients.values()),[]):
        try:
            return client.file.mapping.find_one(dict(name=file_name))["path"].replace("0.0.0.0","localhost")
        except:
            pass
    return None


def article_by_id(aid):
    for db2_client in clients["db2"]:
        try:
            article = db2_client.info.article.find_one(dict(aid=aid))
            # print(article)
            text_file = article["text"]
            
            text_location = convert_file_to_path(text_file).strip()
            print(text_location)

            # Fetch the text content directly like in the original backend
            text = requests.get(text_location).text

            images = [convert_file_to_path(i).strip() for i in article["image"].split(',') if i.strip()]
            videos = [convert_file_to_path(i).strip() for i in article["video"].split(',') if i.strip()]

            return dict(text=text, images=images, videos=videos)
        except:
            pass

def user_by_id(uid):
    for client in sum(list(clients.values()),[]):
        try:
            user = client.info.user.find_one(dict(uid=uid))
            if user:
                user['_id'] = str(user['_id'])
                return user
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

    return dict(message="User Not Found")

def find_user_read_list(uid):
    for client in sum(list(clients.values()),[]):
        try:
            history = list(client.history.read.find(dict(uid=uid)))
            if history:
                return history
        except:
            pass
    return []

def get_popular_rank(grainaty, rid):
    for client in clients["db1" if grainaty=="daily" else "db2"]:
        try:
            rank = client.history.popular_rank.find_one(dict(temporalGranularity=grainaty, id=rid))
            if rank:
                return rank
        except:
            pass
    return None

def get_all_popular_rank(grainaty):
    for client in clients["db1" if grainaty=="daily" else "db2"]:
        try:
            rank = client.history.popular_rank.find(dict(temporalGranularity=grainaty))
            if rank:
                return rank
        except:
            pass
    return []

@app.route("/api/article/<aid>")
def get_article_api(aid: str):
    article_data = article_by_id(aid)
    print(article_data)
    if article_data:
        return article_data
    return {"error": "Article not found"}, 404

@app.route("/api/user/<uid>")
def get_user_api(uid: str):
    user = user_by_id(uid)
    if user.get("message") == "User Not Found":
        return user, 404
    
    history = find_user_read_list(uid)
    history = [dict(
        text=article_by_id(i["aid"])["text"],  # Now this will work because we're getting the actual text
        timestamp=i["timestamp"],
        aid=i["aid"]
    ) for i in history]
    
    return {
        "user": user,
        "reading_history": history
    }

@app.route("/api/popular_rank/<grainaty>/<rid>")
def get_popular_rank_api(grainaty: str, rid: str):
    rid = int(rid)
    rank = get_popular_rank(grainaty, rid)
    if not rank:
        return {"error": "Rank not found"}, 404
    
    rank["article_list"] = [dict(
        text=article_by_id(i)["text"],
        aid=i
    ) for i in rank["articleAidList"]]
    
    timestamp = int(rank["timestamp"]) / 1000
    rank["begin_date"] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    # print(rank)
    del rank["timestamp"]
    del rank["_id"]
    
    return rank


@app.route("/api/popular_rank/<grainaty>")
def get_all_popular_rank_api(grainaty: str):
    ranks = []
    for client in clients["db1" if grainaty=="daily" else "db2"]:
        try:
            ranks.extend(list(client.history.popular_rank.find({"temporalGranularity": grainaty})))
        except:
            pass
            
    if not ranks:
        return {"error": "No ranks found"}, 404

    timestamps = []
    for rank in ranks:
        timestamp = int(rank["timestamp"]) / 1000
        timestamps.append({
            "timestamp": timestamp,
            "date": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
            "rid": rank["id"]
        })
        
    return timestamps

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8070)
