import asyncio
from protocols.http_protocol import run_http_server
from protocols.coap_protocol import start_coap_server
from protocols.websocket_protocol import WebSocketProtocol

def main():
    async def protocols_task():
        protocol_layer = WebSocketProtocol()
        print("Camada de Protocolos iniciada.")

        http_server_task = asyncio.create_task(run_http_server(protocol_layer))
        coap_server_task = asyncio.create_task(start_coap_server(protocol_layer))

        try:
            await asyncio.Event().wait()  # Mantém o loop até o encerramento
        finally:
            print("Camada de Protocolos encerrando...")
            http_server_task.cancel()
            coap_server_task.cancel()
            await asyncio.gather(http_server_task, coap_server_task, return_exceptions=True)
            print("Camada de Protocolos encerrada.")

    asyncio.run(protocols_task())
