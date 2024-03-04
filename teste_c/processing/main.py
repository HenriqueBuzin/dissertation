import asyncio
import json
import os
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient
import redis
import graphene
from aiohttp import web

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("PROCESSING_REDIS_DB", 1))
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

def create_consumption_type():
    return type('Consumption', (graphene.ObjectType,), {
        'id': graphene.String(),
        'date': graphene.String(),
        'time': graphene.String(),
        'consumptionKwhPerMinute': graphene.Float(),
        'type': graphene.String(),
        'meterId': graphene.String(),
    })

def resolve_consumption_data(root, info, **kwargs):
    query = {}
    for key in ['id', 'date', 'time', 'type', 'meterId']:
        if kwargs.get(key) is not None:
            query[key] = kwargs[key]

    data_query = mongo_collection.find(query)
    offset = kwargs.get('offset', None)
    limit = kwargs.get('limit', None)
    if offset is not None:
        data_query = data_query.skip(offset)
    if limit is not None:
        data_query = data_query.limit(limit)

    return [
        {
            'id': str(item["_id"]),
            'date': item["Date"],
            'time': item["Time"],
            'consumptionKwhPerMinute': item["Consumption_kWh_per_minute"],
            'type': item["type"],
            'meterId': item.get("meterId"),
        } for item in data_query
    ]

def create_query_type(Consumption):
    return type('Query', (graphene.ObjectType,), {
        'consumption_data': graphene.List(
            Consumption,
            id=graphene.String(),
            date=graphene.String(),
            time=graphene.String(),
            type=graphene.String(),
            meterId=graphene.String(),
            limit=graphene.Int(),
            offset=graphene.Int(),
            resolver=lambda self, info, **kwargs: resolve_consumption_data(self, info, **kwargs),
        )
    })

ConsumptionType = create_consumption_type()
QueryType = create_query_type(ConsumptionType)
schema = graphene.Schema(query=QueryType)

async def serve_echo():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()

async def graphql_http_handler(request):
    print(f"Solicitação GraphQL recebida: {await request.text()}")
    data = await request.json()
    query = data.get('query')
    variables = data.get('variables')
    result = await schema.execute_async(query, variable_values=variables)
    print(f"Respondendo à solicitação GraphQL com: {json.dumps(result.data)}")
    return web.Response(text=json.dumps(result.data), content_type='application/json')

async def main():
    app = web.Application()
    app.router.add_post('/graphql', graphql_http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8766)
    await site.start()
    await serve_echo()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\Camada de Processamento encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução da Camada de Processamento: {e}")
    finally:
        print("Camada de Processamento encerrado com sucesso.")
