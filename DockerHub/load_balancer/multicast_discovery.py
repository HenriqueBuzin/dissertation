# multicast_discovery.py

from registry import get_available_nodes
import threading
import logging
import asyncio
import socket
import struct
import json
import time

# Configurações do Multicast
MULTICAST_GROUP = "239.0.0.1"
MULTICAST_PORT = 5007
BUFFER_SIZE = 1024

# Lista para armazenar informações dos nós primários conhecidos
known_primary_nodes = {}

def send_multicast_announce(node_id, http_port, coap_port, meter_count, node_count):
    """Envia um anúncio multicast para divulgar este nó primário."""
    message = {
        "node_id": node_id,
        "http_port": http_port,
        "coap_port": coap_port,
        "meters": meter_count,
        "nodes": node_count
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        logging.info(f"Enviando broadcast multicast: {message}")
        sock.sendto(json.dumps(message).encode(), (MULTICAST_GROUP, MULTICAST_PORT))
    finally:
        sock.close()

def listen_multicast():
    """Escuta mensagens multicast para descobrir outros nós primários."""
    global known_primary_nodes

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))

    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(5.0)  # Timeout para evitar travar no recv

    logging.info("Escutando mensagens multicast...")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            try:
                message = json.loads(data.decode())
            except json.JSONDecodeError:
                logging.warning(f"Mensagem inválida recebida de {addr}")
                continue

            node_id = message["node_id"]
            known_primary_nodes[node_id] = {
                "http_port": message["http_port"],
                "coap_port": message["coap_port"],
                "meters": message["meters"],
                "nodes": message["nodes"],
                "ip": addr[0],
                "last_seen": time.time()
            }

            logging.info(f"Nó primário descoberto/atualizado: {node_id} - {known_primary_nodes[node_id]}")

        except socket.timeout:
            # Apenas para manter o loop rodando sem travar
            continue
        except Exception as e:
            logging.error(f"Erro ao processar multicast: {e}")

def start_multicast_listener():
    """Inicia a escuta multicast em uma thread separada."""
    thread = threading.Thread(target=listen_multicast, daemon=True)
    thread.start()

async def multicast_heartbeat(node_id, http_port, coap_port):
    while True:
        available_nodes = get_available_nodes()
        meter_count = sum(len(v) for v in available_nodes.values())
        node_count = len(available_nodes)
        send_multicast_announce(node_id, http_port, coap_port, meter_count, node_count)
        await asyncio.sleep(10)  # Reanuncia a cada 10 segundos
