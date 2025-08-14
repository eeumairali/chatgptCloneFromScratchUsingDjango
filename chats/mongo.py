import uuid 
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from django.conf import settings

_client = MongoClient(settings.MONGO_URI)
db = _client[settings.MONGO_DB]
history = db["history"]  # ONE document per chat

# Index (idempotent)
history.create_index([("user_id", 1), ("updated_at", DESCENDING)])

def new_chat(user_id, title="New chat"):
    cid = uuid.uuid4().hex
    history.insert_one({
        "_id": cid,            # chat id
        "user_id": user_id,    # Django user.id
        "title": title,
        "messages": [],        # [{user:'assistant'|'username', message:'...'}]
        "updated_at": datetime.utcnow()
    })
    return cid

def list_chats(user_id, limit=30):
    # Don’t return messages to keep sidebar light
    return list(history.find(
        {"user_id": user_id}, {"messages": False}
    ).sort("updated_at", DESCENDING).limit(limit))

def get_chat(user_id, cid):
    return history.find_one({"_id": cid, "user_id": user_id})

def push_message(user_id, cid, user, message):
    history.update_one(
        {"_id": cid, "user_id": user_id},
        {
            "$push": {"messages": {"user": user, "message": message}},
            "$set": {"updated_at": datetime.utcnow()}
        },
        upsert=True
    )

