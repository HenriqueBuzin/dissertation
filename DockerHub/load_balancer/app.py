# app.py

from http_server import start_http_server
from coap_server import start_coap_server
from registry import get_available_nodes
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    http_port = 5000
    coap_port = 5683

    logging.info("Starting HTTP and CoAP servers...")

    available_nodes = get_available_nodes()

    await asyncio.gather(
        start_http_server(http_port, available_nodes),
        start_coap_server(coap_port, available_nodes),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nShutting down Load Balancer.")
