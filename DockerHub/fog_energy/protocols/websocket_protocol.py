import asyncio
import json
import websockets
from pymongo import MongoClient
import redis
from protocols.utils import load_env

class WebSocketProtocol:
    def __init__(self):
        env_vars = load_env()
        self.REDIS_HOST = env_vars["REDIS_HOST"]
        self.REDIS_PORT = env_vars["REDIS_PORT"]
        self.PROTOCOLS_REDIS_DB = env_vars["PROTOCOLS_REDIS_DB"]
        self.MONGO_URI = env_vars["MONGO_URI"]
        self.MONGO_DB = env_vars["MONGO_DB"]
        self.PROTOCOLS_PERSIST = env_vars["PROTOCOLS_PERSIST"]
        self.PROTOCOLS_MONGO_COLLECTION = env_vars["PROTOCOLS_MONGO_COLLECTION"]
        
        self.redis_client = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.PROTOCOLS_REDIS_DB, decode_responses=True)
        self.mongo_client = MongoClient(self.MONGO_URI)
        self.mongo_db = self.mongo_client[self.MONGO_DB]
        self.mongo_collection = self.mongo_db[self.PROTOCOLS_MONGO_COLLECTION]
        self.ws_url = 'ws://localhost:8765/'

    async def send_data_websocket(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    await self.send_messages(ws)
            except Exception as e:
                print(f"WebSocket: Erro ao conectar ou enviar dados: {e}. Tentando novamente em 1 segundo...")
                await asyncio.sleep(1)

    async def send_messages(self, ws):
        if self.PROTOCOLS_PERSIST == 1:
            messages = list(self.mongo_collection.find({}))
            for message in messages:
                await ws.send(json.dumps(message, default=str))
                self.mongo_collection.delete_one({"_id": message["_id"]})
        else:
            while self.redis_client.llen("protocols_messages") > 0:
                message = self.redis_client.rpop("protocols_messages")
                await ws.send(message)
        await asyncio.sleep(1)

    def save_message(self, message):
        if self.PROTOCOLS_PERSIST == 1:
            self.mongo_collection.insert_one(message)
        else:
            self.redis_client.lpush("protocols_messages", json.dumps(message))
