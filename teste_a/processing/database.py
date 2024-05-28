from pymongo import MongoClient
import redis
import config

MONGO_URI = f"mongodb://{config.MONGO_USER}:{config.MONGO_PASS}@{config.MONGO_HOST}:{config.MONGO_PORT}/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[config.MONGO_DB]
mongo_collection = mongo_db[config.MONGO_COLLECTION]

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=True)
