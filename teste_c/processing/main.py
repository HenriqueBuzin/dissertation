import asyncio
import websockets

async def echo(websocket):
    async for message in websocket:
        print(f"Mensagem recebida: {message}")
        await websocket.send("Mensagem recebida com sucesso!")

async def main():
    server = await websockets.serve(echo, "localhost", 8765)
    print("Servidor WebSocket iniciado em ws://localhost:8765/")
    
    try:
        await asyncio.Future()  # Mantém o servidor rodando até que uma exceção seja capturada.
    except KeyboardInterrupt:
        pass  # Captura a interrupção do teclado sem fazer nada, mas permite que o código continue.
    
    server.close()
    await server.wait_closed()
    print("\nServidor WebSocket encerrado com sucesso.")

if __name__ == "__main__":
    asyncio.run(main())
