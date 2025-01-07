# processing/main.py

import asyncio
import json
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
    """
    Sobe o servidor HTTP GraphQL na porta 8766
    e o servidor WebSocket na porta 8765.
    """
    # 1) Servidor HTTP (GraphQL)
    app = web.Application()
    app.router.add_post('/graphql', graphql_http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8766)
    await site.start()

    # 2) Servidor WebSocket
    #    Se quiser só localhost, use "127.0.0.1".
    ws_server = await websockets.serve(echo, "0.0.0.0", 8765)
    print("Servidor WebSocket rodando na porta 8765...", flush=True)

    print("Camada de Processamento iniciada.", flush=True)
    try:
        # 3) Mantém o loop ativo indefinidamente
        await asyncio.Event().wait()
    finally:
        print("Camada de Processamento encerrando...", flush=True)
        await runner.cleanup()

        # Fecha o servidor WS
        ws_server.close()
        await ws_server.wait_closed()

        print("Camada de Processamento encerrada.", flush=True)

def main():
    """
    Ponto de entrada da Camada de Processamento.
    """
    asyncio.run(processing_task())

if __name__ == '__main__':
    main()
