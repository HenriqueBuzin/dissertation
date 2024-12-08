import asyncio
from http_server import start_http_server
from coap_server import start_coap_server
import logging

# Configura o log
logging.basicConfig(level=logging.INFO)

async def main():
    http_port = 5000  # Porta HTTP
    coap_port = 5683  # Porta CoAP

    logging.info("Iniciando servidores HTTP e CoAP...")

    # Inicia ambos os servidores em paralelo
    await asyncio.gather(
        start_http_server(http_port),
        start_coap_server(coap_port),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nEncerrando Load Balancer.")
