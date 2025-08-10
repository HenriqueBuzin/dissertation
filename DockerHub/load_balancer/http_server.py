import os
import logging
import asyncio

from aiohttp import web, ClientSession
from docker import from_env as docker_from_env
from registry import (
    register_meter,
    register_node,
    register_load_balancer,
    unregister_load_balancer,
    get_available_nodes,
    get_registered_meters,
    log_current_status,
)

from data_distributor import distribute_data

logging.basicConfig(level=logging.INFO)

SELF          = os.environ["SELF_NAME"]      # ex: "bairro1_load_balancer_1"
LABEL         = os.environ["LB_TYPE_ID"]     # ex: "3"
INTERNAL_PORT = 5000                         # porta interna do container

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
    """Envia um dado para um peer específico."""
    url = f"http://{peer}:{INTERNAL_PORT}/receive_data"
    try:
        async with ClientSession() as sess:
            await sess.post(url, json=data)
            logging.info(f"[OFFLOAD] enviado → {peer}")
    except Exception as e:
        logging.error(f"Falha envio para {peer}: {e}")

async def distribute_to_local_nodes(data, dtype):
    """Envia o dado para os fog‑nodes locais."""
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

# --- Handlers HTTP ---

async def handle_root(req):
    return web.Response(text="LB OK", status=200)

async def handle_status(req):
    avail = get_available_nodes()
    return web.json_response({"fog_nodes": {k: len(v) for k, v in avail.items()}})

async def handle_receive_data(req):
    data = await req.json()
    logging.info(f"[HTTP ← RECEIVE] {data}")

    # 1) Auto‑registro do medidor
    mtype = data.get("type")
    mid   = data.get("id")
    street = data.get("street")
    if mtype and mid and street:
        if register_meter(mid, street, mtype):
            log_current_status()

    # 2) Identifica campo consumption_*
    dtype = next((k for k in data if k.startswith("consumption_")), None)
    if not dtype:
        return web.json_response({"error": "tipo não identificado"}, status=400)

    # 3) Quantidades locais
    local_nodes_count  = len(get_available_nodes().get(dtype, []))
    local_meters_count = len(get_registered_meters().get(mtype, []))

    # 4) Se há fog‑nodes locais suficientes, distribui localmente
    if local_nodes_count > 0 and local_meters_count <= local_nodes_count:
        await distribute_to_local_nodes(data, dtype)
        return web.json_response({"status": "distribuído localmente"})

    # 5) Senão, tenta offload para outro LB com capacidade sobrando
    peers = discover_peers()
    if not peers:
        logging.debug("Nenhum outro LB para offload; pulando")
        return web.json_response({"status": "nenhum destino disponível"})

    # coleta status de fog_nodes de cada peer
    capacities = {}
    for p in peers:
        st = await fetch_status(p)
        if st and "fog_nodes" in st:
            capacities[p] = st["fog_nodes"].get(dtype, 0)

    # seleciona peers com mais nós do que meus medidores
    candidates = [p for p, cap in capacities.items() if cap > local_meters_count]
    if not candidates and capacities:
        # se nenhum tem capacidade “excedente”, escolhe o que tem mais nós
        best = max(capacities, key=lambda p: capacities[p])
        candidates = [best]

    # offload para os candidatos
    for p in candidates:
        await send_to_peer(p, data)

    return web.json_response({"status": f"offloaded para {candidates}"})

async def handle_register_node(req):
    d = await req.json()
    ok = register_node(d.get("node_id"), d.get("data_type"), d.get("node_endpoint"))
    return web.json_response(
        {"status": "node registered"} if ok else {"error": "failed to register node"},
        status=(200 if ok else 400)
    )

async def handle_register_meter(req):
    d = await req.json()
    ok = register_meter(d.get("id"), d.get("street"), d.get("type"))
    return web.json_response(
        {"status": "meter registered"} if ok else {"error": "failed to register meter"},
        status=(200 if ok else 400)
    )

async def handle_register_lb(req):
    d = await req.json()
    register_load_balancer(d.get("node_id"), d.get("ip"), d.get("http_port"))
    return web.json_response({"status": "lb registered"})

async def handle_unregister_lb(req):
    d = await req.json()
    unregister_load_balancer(d.get("node_id"))
    return web.json_response({"status": "lb unregistered"})

async def handle_get_meters(request):
    """
    Retorna o dicionário com todos os medidores registrados,
    agrupados por tipo ("energy", "water").
    """
    meters = get_registered_meters()  # :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
    return web.json_response(meters)

async def start_http_server(port):
    app = web.Application()
    app.router.add_get("/",                          handle_root)
    app.router.add_get("/status",                    handle_status)
    app.router.add_post("/receive_data",             handle_receive_data)
    app.router.add_post("/register_node",            handle_register_node)
    app.router.add_post("/receive_data/register_meter", handle_register_meter)
    app.router.add_post("/register_load_balancer",   handle_register_lb)
    app.router.add_post("/unregister_load_balancer", handle_unregister_lb)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"HTTP rodando em {port}")
    await asyncio.get_event_loop().create_future()
