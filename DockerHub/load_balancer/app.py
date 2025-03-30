# app.py

from multicast_discovery import send_multicast_announce, start_multicast_listener, multicast_heartbeat
from http_server import start_http_server
from coap_server import start_coap_server
from registry import get_available_nodes
import asyncio
import logging
import socket

logging.basicConfig(level=logging.INFO)

async def main():
    http_port = 5000
    coap_port = 5683

    # Obtém o nome do host para identificar o nó primário
    node_id = socket.gethostname()

    # Inicia a escuta multicast
    start_multicast_listener()

    # Pequena espera para garantir que o multicast receba mensagens antes de anunciar
    await asyncio.sleep(2)

    # Obtém informações sobre os nós disponíveis
    available_nodes = get_available_nodes()
    meter_count = sum(len(v) for v in available_nodes.values())
    node_count = len(available_nodes)

    # Faz o broadcast multicast anunciando este nó
    send_multicast_announce(node_id, http_port, coap_port, meter_count, node_count)

    logging.info("Starting HTTP, CoAP servers and Heartbeat...")

    available_nodes = get_available_nodes()

    await asyncio.gather(
        start_http_server(http_port, available_nodes),
        start_coap_server(coap_port, available_nodes),
        multicast_heartbeat(node_id, http_port, coap_port)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nShutting down Load Balancer.")
