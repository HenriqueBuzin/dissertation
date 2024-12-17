import asyncio
from aiohttp import web
import json
from processing.graphql_schema import schema

async def graphql_http_handler(request):
    data = await request.json()
    query = data.get('query')
    variables = data.get('variables')
    result = await schema.execute_async(query, variable_values=variables)
    return web.Response(text=json.dumps(result.data), content_type='application/json')

def main():
    async def processing_task():
        app = web.Application()
        app.router.add_post('/graphql', graphql_http_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8766)
        await site.start()

        print("Camada de Processamento iniciada.", flush=True)
        try:
            await asyncio.Event().wait()  # Mantém o loop até o encerramento
        finally:
            print("Camada de Processamento encerrando...", flush=True)
            await runner.cleanup()
            print("Camada de Processamento encerrada.", flush=True)

    asyncio.run(processing_task())
