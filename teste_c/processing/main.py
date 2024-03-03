import asyncio
import json
import os
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient
import redis
import graphene

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

class Consumption(graphene.ObjectType):
    id = graphene.String()
    date = graphene.String()
    time = graphene.String()
    consumptionKwhPerMinute = graphene.Float()
    type = graphene.String()

class Query(graphene.ObjectType):
    consumption_data = graphene.List(
        Consumption,
        id=graphene.String(),
        date=graphene.String(),
        time=graphene.String(),
        type=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )

    def resolve_consumption_data(self, info, id=None, date=None, time=None, type=None, limit=None, offset=None):
        query = {}
        if id is not None:
            query['id'] = id
        if date is not None:
            query['Date'] = date
        if time is not None:
            query['Time'] = time
        if type is not None:
            query['type'] = type

        data_query = mongo_collection.find(query)
        if offset is not None:
            data_query = data_query.skip(offset)
        if limit is not None:
            data_query = data_query.limit(limit)

        return [
            Consumption(
                date=item["Date"],
                time=item["Time"],
                consumptionKwhPerMinute=float(item["Consumption_kWh_per_minute"]),
                type=item["type"],
                id=str(item["id"])
            ) for item in data_query
        ]

schema = graphene.Schema(query=Query)

async def echo2(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
            query = data.get("query")
            variables = data.get("variables", {})

            result = await schema.execute_async(query, variable_values=variables)

            print(result)
                    
            await websocket.send(json.dumps(result.data))
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")
            await websocket.send(json.dumps({"error": "Erro ao processar a consulta"}))

async def serve_echo():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()

async def serve_echo2():
    async with websockets.serve(echo2, "localhost", 8766):
        await asyncio.Future()

async def main():
    await asyncio.gather(
        serve_echo(),
        serve_echo2()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor WebSocket encerrado pelo usuário.")
