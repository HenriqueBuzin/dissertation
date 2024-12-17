import asyncio
from aiohttp import web
import json
from processing.graphql_schema import schema

async def graphql_http_handler(request):
    print(f"Solicitação GraphQL recebida: {await request.text()}", flush=True)
    data = await request.json()
    query = data.get('query')
    variables = data.get('variables')
    result = await schema.execute_async(query, variable_values=variables)
    print(f"Respondendo à solicitação GraphQL com: {json.dumps(result.data)}", flush=True)
    return web.Response(text=json.dumps(result.data), content_type='application/json')

async def main():
    app = web.Application()
    app.router.add_post('/graphql', graphql_http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8766)
    await site.start()
    from websocket_handler import serve_echo
    await serve_echo()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCamada de Processamento encerrando...", flush=True)
    except Exception as e:
        print(f"\nErro durante a execução da Camada de Processamento: {e}", flush=True)
    finally:
        print("Camada de Processamento encerrado com sucesso.", flush=True)
