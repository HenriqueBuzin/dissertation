# protocols/main.py

import asyncio
from protocols.http_protocol import run_http_server
from protocols.coap_protocol import start_coap_server
from protocols.websocket_protocol import WebSocketProtocol

def main():
    async def protocols_task():
        protocol_layer = WebSocketProtocol()
        print("Camada de Protocolos iniciada.", flush=True)

        # Lançando tarefas assíncronas
        http_server_task = asyncio.create_task(run_http_server(protocol_layer))
        coap_server_task = asyncio.create_task(start_coap_server(protocol_layer))
        websocket_task = asyncio.create_task(protocol_layer.send_data_websocket())

        try:
            # Mantém o loop em execução indefinidamente
            await asyncio.Event().wait()
        finally:
            print("Camada de Protocolos encerrando...", flush=True)
            http_server_task.cancel()
            coap_server_task.cancel()
            websocket_task.cancel()

            # Garante que todas as tasks sejam encerradas corretamente
            await asyncio.gather(
                http_server_task,
                coap_server_task,
                websocket_task,
                return_exceptions=True
            )
            print("Camada de Protocolos encerrada.", flush=True)

    asyncio.run(protocols_task())

if __name__ == "__main__":
    main()
