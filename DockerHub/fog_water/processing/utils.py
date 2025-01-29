# processing/utils.py

import json
from processing import config
from processing.database import mongo_collection, redis_client

def save_message(message):
    if config.PROCESSING_PERSIST == 1:
        mongo_collection.insert_one(json.loads(message))
        print("Mensagem salva no MongoDB.", flush=True)
    else:
        redis_client.lpush("messages", message)
        print("Mensagem salva no Redis.", flush=True)
