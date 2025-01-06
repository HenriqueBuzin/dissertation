# processing/websocket_handler.py

import asyncio
import websockets
from processing.utils import save_message

async def echo(websocket):
    """
    Recebe mensagens, salva no banco (via save_message), e responde.
    """
    try:
        async for message in websocket:
            print(f"Mensagem recebida: {message}", flush=True)
            # Salva num executor para não travar o event loop
            await asyncio.get_running_loop().run_in_executor(None, save_message, message)
            try:
                await websocket.send("Mensagem recebida e processada com sucesso.")
            except websockets.exceptions.ConnectionClosedOK:
                pass
    except Exception as e:
        print(f"Erro inesperado: {e}", flush=True)
