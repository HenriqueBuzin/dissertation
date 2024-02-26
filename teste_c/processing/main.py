import asyncio
import websockets
import signal

async def echo(websocket):
    async for message in websocket:
        print(f"Mensagem recebida: {message}")
        await websocket.send("Mensagem recebida com sucesso!")

async def main():
    server = await websockets.serve(echo, "localhost", 8765)
    print("Servidor WebSocket iniciado em ws://localhost:8765/")
    
    stop = asyncio.Future()
    asyncio.get_running_loop().add_signal_handler(signal.SIGINT, stop.set_result, None)
    await stop

    server.close()
    await server.wait_closed()
    print("\nServidor WebSocket encerrado com sucesso.")

if __name__ == "__main__":
    asyncio.run(main())
