import asyncio
import threading
from websocket_protocol import WebSocketProtocol
from http_protocol import run_http_server
from coap_protocol import start_coap_server

async def main():
    protocol_layer = WebSocketProtocol()
    http_thread = threading.Thread(target=lambda: run_http_server(protocol_layer), daemon=True)
    http_thread.start()
    await start_coap_server(protocol_layer)
    await protocol_layer.send_data_websocket()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCamada de Protocolos encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução da Camada de Protocolos: {e}")
    finally:
        print("Camada de Protocolos encerrada com sucesso.")
