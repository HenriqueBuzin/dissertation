# protocols/http_protocol.py

import time
import asyncio
from aiohttp import web
from protocols.sftp_handler import handle_sftp_details_and_send

async def run_http_server(protocol_layer):
    
    async def handle_post(request):
        try:
            message = await request.json()
        except Exception as e:
            print(f"Erro ao decodificar JSON: {e}", flush=True)
            return web.Response(status=400, text="HTTP: Error decoding JSON")

        print("Recebendo mensagem HTTP...", flush=True)
        print(f"Dados HTTP recebidos: {message}", flush=True)

        message_type = message.get('type')

        if message_type == 'consumption':
            print("Processando dados de consumo...", flush=True)
            protocol_layer.save_message(message)
            return web.Response(status=200, text="HTTP: Consumption data received")

        elif message_type == 'ftp':
            print("Processando detalhes do FTP...", flush=True)

            start = time.time()
            await handle_sftp_details_and_send(message)
            end = time.time()

            elapsed = end - start
            print(f"[MÉTRICA] Tempo de envio para o aggregator via SFTP: {elapsed:.4f}s", flush=True)

            return web.Response(status=200, text="HTTP: FTP details received")

        else:
            return web.Response(status=400, text="HTTP: Unknown message type")

    app = web.Application()

    app.router.add_post('/receive_data', handle_post)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=8000)
    print("HTTP: Servidor HTTP rodando na porta 8000...", flush=True)
    await site.start()

    await asyncio.Event().wait()
