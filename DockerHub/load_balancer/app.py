# app.py

import os
import asyncio
import logging

from http_server import start_http_server
from coap_server import start_coap_server
from mqtt_server import start_mqtt_server

logging.basicConfig(level=logging.INFO)

async def main():
    http_port = int(os.environ.get("HTTP_PORT", 5000))
    coap_port = int(os.environ.get("COAP_PORT", 5683))
    mqtt_port = int(os.environ.get("MQTT_PORT", 1883))

    # Roda HTTP e CoAP em paralelo
    await asyncio.gather(
        start_http_server(http_port),
        start_coap_server(coap_port),
        # start_mqtt_server(mqtt_port)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Load Balancer encerrando...")
