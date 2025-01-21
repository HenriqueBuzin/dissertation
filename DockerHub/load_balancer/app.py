# app.py

import asyncio
from http_server import start_http_server
from coap_server import start_coap_server
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    http_port = 5000  # HTTP Port
    coap_port = 5683  # CoAP Port

    logging.info("Starting HTTP and CoAP servers...")

    # Initialize the structure to track available nodes
    available_nodes = {
        "consumption_kwh_per_hour": [],
        "consumption_m3_per_hour": [],
        # Adicione outros tipos específicos conforme necessário
    }

    # Start both servers concurrently, passing available_nodes
    await asyncio.gather(
        start_http_server(http_port, available_nodes),
        start_coap_server(coap_port, available_nodes),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nShutting down Load Balancer.")
