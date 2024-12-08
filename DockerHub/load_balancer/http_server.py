from aiohttp import web
import logging

# Configura o log
logging.basicConfig(level=logging.INFO)

# Endpoint para receber dados via HTTP
async def handle_receive_data(request):
    try:
        data = await request.json()
        logging.info(f"HTTP: Dados recebidos: {data}")
        return web.json_response({"status": "HTTP: Dados recebidos com sucesso"})
    except Exception as e:
        logging.error(f"Erro no servidor HTTP: {e}")
        return web.json_response({"status": "Erro no servidor HTTP"}, status=500)

# Inicia o servidor HTTP
async def start_http_server(port):
    app = web.Application()
    app.router.add_post("/receive_data", handle_receive_data)

    logging.info(f"HTTP: Servidor rodando na porta {port}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)  # Certifique-se de ouvir em "0.0.0.0"
    await site.start()
