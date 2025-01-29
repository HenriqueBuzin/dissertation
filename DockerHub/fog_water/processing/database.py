# processing/database.py

import redis
from processing import config
from pymongo import MongoClient

print("Carregando configurações...", flush=True)
print(f"MONGO_HOST: {config.MONGO_HOST}", flush=True)
print(f"MONGO_PORT: {config.MONGO_PORT}", flush=True)
print(f"MONGO_USER: {config.MONGO_USER}", flush=True)
print(f"MONGO_PASS: {config.MONGO_PASS}", flush=True)
print(f"MONGO_DB: {config.MONGO_DB}", flush=True)
print(f"MONGO_COLLECTION: {config.MONGO_COLLECTION}", flush=True)
print(f"REDIS_HOST: {config.REDIS_HOST}", flush=True)
print(f"REDIS_PORT: {config.REDIS_PORT}", flush=True)
print(f"REDIS_DB: {config.REDIS_DB}", flush=True)

MONGO_URI = f"mongodb://{config.MONGO_USER}:{config.MONGO_PASS}@{config.MONGO_HOST}:{config.MONGO_PORT}/"
print(f"\nTentando conectar ao MongoDB com URI: {MONGO_URI}", flush=True)

try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[config.MONGO_DB]
    mongo_collection = mongo_db[config.MONGO_COLLECTION]
    print("Conexão com MongoDB bem-sucedida!", flush=True)
    print("Coleções disponíveis no banco:", mongo_db.list_collection_names(), flush=True)
except Exception as e:
    print(f"Erro ao conectar ao MongoDB: {e}", flush=True)

print(f"\nTentando conectar ao Redis em {config.REDIS_HOST}:{config.REDIS_PORT}, DB={config.REDIS_DB}", flush=True)
try:
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=True
    )
    redis_client.set("test_key", "connection_successful")
    print("Conexão com Redis bem-sucedida!", flush=True)
    print("Valor salvo no Redis (test_key):", redis_client.get("test_key"), flush=True)
except Exception as e:
    print(f"Erro ao conectar ao Redis: {e}", flush=True)
