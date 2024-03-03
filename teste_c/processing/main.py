import asyncio
import json
import os
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient
import redis

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("PROCESSING_REDIS_DB", 0))
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "mydatabase")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
mongo_collection = mongo_db["messages"]

PROCESSING_PERSIST = int(os.getenv("PROCESSING_PERSIST", 0))

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
mongo_collection = mongo_db["messages"]

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def save_message(message):
    if PROCESSING_PERSIST == 1:
        mongo_collection.insert_one(json.loads(message))
        print("Mensagem salva no MongoDB.")
    else:
        redis_client.lpush("messages", message)
        print("Mensagem salva no Redis.")

async def echo(websocket):
    try:
        async for message in websocket:
            print(f"Mensagem recebida: {message}")
            await asyncio.get_event_loop().run_in_executor(None, save_message, message)
            try:
                await websocket.send("Mensagem recebida e processada com sucesso.")
            except websockets.exceptions.ConnectionClosedOK:
                pass
    except Exception as e:
        print(f"Erro inesperado: {e}")

async def main():
    async with websockets.serve(echo, "localhost", 8765):
        print("Servidor WebSocket iniciado em ws://localhost:8765/")
        await asyncio.Future()  # Mantém o servidor em execução

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor WebSocket encerrado pelo usuário.")
