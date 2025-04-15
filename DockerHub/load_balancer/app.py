# app.py

import requests
import asyncio
import logging
import socket

from http_server import start_http_server
from coap_server import start_coap_server
from registry import (
    get_available_nodes,
    register_load_balancer,
    unregister_load_balancer,
    get_load_balancers,
    log_current_status
)

logging.basicConfig(level=logging.INFO)

# --------------------------------------------------
# Função auxiliar para IP local
# --------------------------------------------------

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# --------------------------------------------------
# Registro de LB ao iniciar e ao desligar
# --------------------------------------------------

async def register_self(http_port):
    node_id = socket.gethostname()
    ip = get_local_ip()
    register_load_balancer(node_id, ip, http_port)
    logging.info(f"[BOOT] Registrado localmente LB {node_id} ({ip}:{http_port})")

async def unregister_self():
    node_id = socket.gethostname()
    peers = get_load_balancers()
    for peer_id, info in peers.items():
        try:
            if peer_id == node_id:
                continue
            requests.post(
                f"http://{info['ip']}:{info['http_port']}/unregister_load_balancer",
                json={"node_id": node_id},
                timeout=2
            )
        except:
            continue
    unregister_load_balancer(node_id)
    logging.info(f"[SHUTDOWN] LB {node_id} removido da lista local.")

# --------------------------------------------------
# Função principal
# --------------------------------------------------

async def main():
    http_port = 5000
    coap_port = 5683

    await register_self(http_port)

    log_current_status()  # agora importado do registry

    available_nodes = get_available_nodes()

    await asyncio.gather(
        start_http_server(http_port, available_nodes),
        start_coap_server(coap_port, available_nodes),
    )

# --------------------------------------------------
# Execução
# --------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Encerrando Load Balancer...")
        asyncio.run(unregister_self())
