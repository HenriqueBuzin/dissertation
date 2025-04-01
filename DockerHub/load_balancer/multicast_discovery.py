# multicast_discovery.py

import threading
import logging
import asyncio
import socket
import struct
import json
import time

known_primary_nodes = {}

MULTICAST_GROUP = "239.0.0.1"
MULTICAST_PORT = 5007
BUFFER_SIZE = 1024

def send_multicast_announce(node_id, http_port, coap_port, stats):
    """
    stats: dict com:
      - 'registered_meters'
      - 'fog_nodes_agua'
      - 'fog_nodes_energia'
      - 'specialties_count'
      etc.
    """
    
    ip = get_local_ip()  # Pega IP do container

    message = {
        "node_id": node_id,
        "http_port": http_port,
        "coap_port": coap_port,
        "registered_meters": stats["registered_meters"],

        # Exemplo: se quiser exibir contadores separados
        "energy_meters": stats["energy_meters"],
        "water_meters":  stats["water_meters"],

        "fog_nodes_energia": stats["fog_nodes_energy"],
        "fog_nodes_agua":    stats["fog_nodes_water"],

        "ip": ip
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        logging.info(f"Enviando broadcast multicast: {message}")
        sock.sendto(json.dumps(message).encode(), (MULTICAST_GROUP, MULTICAST_PORT))
    finally:
        sock.close()

def listen_multicast():
    print("[BROADCAST] Escutando mensagens multicast...", flush=True)

    global known_primary_nodes

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))

    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(5.0)

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
                # mudamos 'meters' => 'registered_meters', etc.
                "registered_meters": message.get("registered_meters", 0),
                "fog_nodes_agua": message.get("fog_nodes_agua", 0),
                "fog_nodes_energia": message.get("fog_nodes_energia", 0),
                "specialties_count": message.get("specialties_count", 0),
                "ip": message["ip"],
                "last_seen": time.time()
            }

            logging.info(f"Nó primário descoberto/atualizado: {node_id} - {known_primary_nodes[node_id]}")

            print(
                f"[BROADCAST] Nó descoberto: {node_id} — IP {message['ip']}"
                f" — HTTP: {message['http_port']} — CoAP: {message['coap_port']}"
                f" — Medidores: {message.get('registered_meters', 0)}"
                f" — Fog Água: {message.get('fog_nodes_agua', 0)}"
                f" — Fog Energia: {message.get('fog_nodes_energia', 0)}"
                f" — Especialidades: {message.get('specialties_count', 0)}",
                flush=True
            )

        except socket.timeout:
            continue
        except Exception as e:
            logging.error(f"Erro ao processar multicast: {e}")

def start_multicast_listener():
    thread = threading.Thread(target=listen_multicast, daemon=True)
    thread.start()

async def multicast_heartbeat(node_id, http_port, coap_port):
    from registry import get_available_nodes
    from app import gather_stats

    while True:
        # Recalcula stats a cada batida
        available_nodes = get_available_nodes()
        stats = gather_stats(available_nodes)

        # Agora chamamos com stats
        send_multicast_announce(node_id, http_port, coap_port, stats)
        await asyncio.sleep(10)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
