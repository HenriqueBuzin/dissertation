# data_distributor.py

import os
import logging
from aiohttp import ClientSession
from docker import from_env as docker_from_env
from registry import register_meter, log_current_status, get_available_nodes, get_registered_meters

SELF = os.environ["SELF_NAME"]
LABEL = os.environ["LB_TYPE_ID"]
INTERNAL_PORT = 5000

def discover_peers():
    client = docker_from_env()
    containers = client.containers.list(filters={"label": f"type={LABEL}"})
    return [c.name for c in containers if c.name != SELF]

async def fetch_status(peer):
    url = f"http://{peer}:{INTERNAL_PORT}/status"
    try:
        async with ClientSession() as sess:
            async with sess.get(url, timeout=2) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        logging.warning(f"Falha ao obter status de {peer}")
    return None

async def send_to_peer(peer, data):
    url = f"http://{peer}:{INTERNAL_PORT}/receive_data"
    try:
        async with ClientSession() as sess:
            await sess.post(url, json=data)
            logging.info(f"[OFFLOAD] enviado → {peer}")
    except Exception as e:
        logging.error(f"Falha envio para {peer}: {e}")

async def distribute_to_local_nodes(data, dtype):
    local = get_available_nodes().get(dtype, [])
    if not local:
        return

    payload = {
        "type":   "consumption",
        "id":     data.get("id"),
        "street": data.get("street"),
        dtype:    data[dtype],
        "date":   data.get("date"),
        "time":   data.get("time"),
    }

    for node in local:
        endpoint = node["node_endpoint"]
        try:
            async with ClientSession() as sess:
                await sess.post(endpoint, json=payload)
                logging.info(f"[LOCAL] enviado → {node['node_id']}")
        except Exception as e:
            logging.error(f"Falha envio local para {node['node_id']}: {e}")

async def distribute_data(data):
    mtype = data.get("type")
    mid = data.get("id")
    street = data.get("street")
    if mtype and mid and street:
        if register_meter(mid, street, mtype):
            log_current_status()

    dtype = next((k for k in data if k.startswith("consumption_")), None)
    if not dtype:
        return

    await distribute_to_local_nodes(data, dtype)

    peers = discover_peers()
    for peer in peers:
        await send_to_peer(peer, data)
