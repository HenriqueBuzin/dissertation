import asyncio
import websockets
from processing.utils import save_message

async def echo(websocket):
    try:
        async for message in websocket:
            print(f"Mensagem recebida: {message}", flush=True)
            await asyncio.get_event_loop().run_in_executor(None, save_message, message)
            try:
                await websocket.send("Mensagem recebida e processada com sucesso.")
            except websockets.exceptions.ConnectionClosedOK:
                pass
    except Exception as e:
        print(f"Erro inesperado: {e}", flush=True)

async def serve_echo():
    async with websockets.serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()
