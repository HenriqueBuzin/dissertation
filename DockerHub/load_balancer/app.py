# app.py

import asyncio
import logging
import socket
import os
import requests

# Imports do seu código
from multicast_discovery import (
    send_multicast_announce,
    start_multicast_listener,
    multicast_heartbeat
)
from http_server import start_http_server
from coap_server import start_coap_server
from registry import get_registered_meters, get_available_nodes

logging.basicConfig(level=logging.INFO)

# --- Variáveis de ambiente para peers (DNS de outros LBs) ---
LB_PEERS_STR = os.getenv("LB_PEERS", "")  # ex.: "Canasvieiras_load_balancer_1,Jurere_load_balancer_1"
PEER_LIST = [p.strip() for p in LB_PEERS_STR.split(",") if p.strip()]

from registry import get_registered_meters, get_available_nodes

def gather_stats(available_nodes):
    """
    Retorna estatísticas detalhadas:
      - registered_meters: total de medidores (soma de 'energy' + 'water')
      - energy_meters, water_meters: quantidades separadas
      - fog_nodes_energy, fog_nodes_water: nós de névoa de cada tipo
    """

    # registered = { "energy": [...], "water": [...] }
    registered = get_registered_meters()  
    
    # nodes = { "consumption_kwh_per_hour": [...], "consumption_m3_per_hour": [...] }
    # Mas vamos usar o 'available_nodes' que foi passado e pode ser o mesmo dict retornado por get_available_nodes()
    nodes = available_nodes

    # Conta quantos medidores de energia e água existem registrados
    energy_count = len(registered.get("energy", []))
    water_count  = len(registered.get("water", []))

    # Soma total de medidores
    total_meters = energy_count + water_count

    # Conta fog nodes de energia e água
    fog_energy = len(nodes.get("consumption_kwh_per_hour", []))
    fog_water  = len(nodes.get("consumption_m3_per_hour", []))

    return {
        "registered_meters": total_meters,
        "energy_meters":     energy_count,
        "water_meters":      water_count,
        "fog_nodes_energy":  fog_energy,
        "fog_nodes_water":   fog_water,
    }

def log_current_status():
    """
    Exibe no log a contagem de medidores e de fog nodes,
    separando água e energia.
    """
    available_nodes = get_available_nodes()
    s = gather_stats(available_nodes)
    logging.info(
        "[STATUS] Medidores -> "
        f"ENERGIA={s['energy_meters']} | "
        f"ÁGUA={s['water_meters']}"
    )
    logging.info(
        "[STATUS] FogNodes -> "
        f"ENERGIA={s['fog_nodes_energy']} | "
        f"ÁGUA={s['fog_nodes_water']}"
    )

async def communicate_with_peers_loop():
    """
    Loop que a cada 10s tenta se comunicar com peers via HTTP na porta 5000,
    apenas para demonstrar a ideia de 'checar' se outros LBs respondem.
    """
    local_name = socket.gethostname()  # nome deste container

    # Log inicial para debug, mostrando que peers (LB_PEERS) foram configurados
    logging.info(f"[DEBUG] Lista de peers (LB_PEERS): {PEER_LIST}")

    while True:
        for peer in PEER_LIST:
            if peer == local_name:
                continue  # não tenta se comunicar consigo mesmo
            url = f"http://{peer}:5000/"
            try:
                resp = requests.get(url, timeout=2)
                logging.info(f"[{local_name}] falou com {peer}, status={resp.status_code}")
            except Exception as e:
                logging.warning(f"[{local_name}] falha ao comunicar com {peer}: {e}")

        await asyncio.sleep(10)

async def main():
    """
    Função principal que inicia:
      - Escuta Multicast
      - HTTP server
      - CoAP server
      - Heartbeat (anúncios Multicast)
      - Loop de comunicação com peers
    E também faz log das estatísticas de medidores/fog nodes.
    """

    http_port = 5000
    coap_port = 5683

    # Nome do container (serve de ID principal)
    node_id = socket.gethostname()

    # 1) Inicia a escuta multicast em background
    start_multicast_listener()

    # 2) Aguarda um pouco para receber possíveis anúncios de outros
    await asyncio.sleep(2)

    # 3) Calcula estatísticas atuais do registry
    available_nodes = get_available_nodes()
    stats = gather_stats(available_nodes)

    # Exemplo de log das estatísticas
    log_current_status()

    # 4) Faz o broadcast multicast anunciando este LB + stats
    #    Nota: Se seu send_multicast_announce(...) original aceitava
    #          fewer/more args, ajuste conforme seu multicast_discovery.py
    send_multicast_announce(
        node_id=node_id,
        http_port=http_port,
        coap_port=coap_port,
        stats=stats  # ou se preferir, injetar chaves: "registered_meters", etc.
    )

    logging.info("Starting HTTP, CoAP servers and Heartbeat...")

    # 5) Pega (opcionalmente) again o available_nodes atualizado
    #    se quiser logar novamente ou mandar no heartbeat
    available_nodes = get_available_nodes()

    # 6) Executa em paralelo:
    #    - HTTP server
    #    - CoAP server
    #    - Heartbeat Multicast (que periodicamente chama send_multicast_announce)
    #    - Loop de comunicação com peers
    await asyncio.gather(
        start_http_server(http_port, available_nodes),
        start_coap_server(coap_port, available_nodes),
        multicast_heartbeat(node_id, http_port, coap_port),
        communicate_with_peers_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nShutting down Load Balancer.")
