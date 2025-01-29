# processing/main.py

import json
import asyncio
import websockets
from aiohttp import web
from processing.graphql_schema import schema
from processing.websocket_handler import echo

async def graphql_http_handler(request):
    print(f"Solicitação GraphQL recebida: {await request.text()}", flush=True)
    data = await request.json()
    query = data.get('query')
    variables = data.get('variables')
    result = await schema.execute_async(query, variable_values=variables)
    print(f"Respondendo à solicitação GraphQL com: {json.dumps(result.data)}", flush=True)
    return web.Response(
        text=json.dumps(result.data),
        content_type='application/json'
    )

async def processing_task():

    app = web.Application()
    app.router.add_post('/graphql', graphql_http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8766)
    await site.start()

    ws_server = await websockets.serve(echo, "0.0.0.0", 8765)
    print("Servidor WebSocket rodando na porta 8765...", flush=True)

    print("Camada de Processamento iniciada.", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        print("Camada de Processamento encerrando...", flush=True)
        await runner.cleanup()

        ws_server.close()
        await ws_server.wait_closed()

        print("Camada de Processamento encerrada.", flush=True)

def main():
    asyncio.run(processing_task())

if __name__ == '__main__':
    main()
