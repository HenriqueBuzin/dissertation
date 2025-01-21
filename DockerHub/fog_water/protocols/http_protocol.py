# protocols/http_protocol.py

import os
import asyncio
from aiohttp import web
from protocols.sftp_handler import handle_sftp_details_and_send

async def run_http_server(protocol_layer):
    """
    Cria e inicia um servidor HTTP assíncrono usando aiohttp.
    """

    async def handle_post(request):
        """
        Esta função lida com requisições POST na rota '/receive_data'.
        """
        try:
            # Lê o body como JSON
            message = await request.json()
        except Exception as e:
            print(f"Erro ao decodificar JSON: {e}", flush=True)
            return web.Response(status=400, text="HTTP: Error decoding JSON")

        print("Recebendo mensagem HTTP...", flush=True)
        print(f"Dados HTTP recebidos: {message}", flush=True)

        # Identifica o tipo da mensagem
        message_type = message.get('type')

        # Fluxo de decisão com base no tipo
        if message_type == 'consumption':
            print("Processando dados de consumo...", flush=True)
            # Salva na camada de protocolo (Mongo ou Redis)
            protocol_layer.save_message(message)
            return web.Response(status=200, text="HTTP: Consumption data received")

        elif message_type == 'ftp':
            print("Processando detalhes do FTP...", flush=True)
            # Se handle_sftp_details_and_send for assíncrono:
            await handle_sftp_details_and_send(message)
            return web.Response(status=200, text="HTTP: FTP details received")

        else:
            return web.Response(status=400, text="HTTP: Unknown message type")

    # Cria a aplicação aiohttp
    app = web.Application()

    # Ajuste a rota para '/receive_data'
    app.router.add_post('/receive_data', handle_post)

    # Configura e inicia o servidor na porta 8000
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=8000)
    print("HTTP: Servidor HTTP rodando na porta 8000...", flush=True)
    await site.start()

    # Mantém a corrotina "viva" até o cancelamento ou encerramento manual
    await asyncio.Event().wait()
