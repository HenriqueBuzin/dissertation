import asyncio
import websockets

async def echo(websocket, path):
    async for message in websocket:
        print(f"Mensagem recebida: {message}")
        await websocket.send("Mensagem recebida com sucesso!")

async def main():
    async with websockets.serve(echo, "localhost", 8765):
        print("Servidor WebSocket iniciado em ws://localhost:8765/")
        await asyncio.Future()  # Mantém o servidor em execução até que algo externo cancele essa Future.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServidor WebSocket encerrando...")
    finally:
        # Neste ponto, o `asyncio.run()` já tratou do encerramento do loop de eventos.
        print("Servidor WebSocket encerrado com sucesso.")
