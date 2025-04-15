# http_server.py

from registry import log_current_status
from aiohttp import web, ClientSession
import functools
import logging
import asyncio
import time
from registry import (
    register_meter,
    register_load_balancer,
    unregister_load_balancer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# -------------------
# Funções auxiliares
# -------------------

def determine_data_type(data):
    keys = list(data.keys())
    last_key = keys[-1] if keys else None
    if last_key and last_key.startswith('consumption_'):
        return last_key
    return None

# -------------------------------
# Distribuição de dados para nós
# -------------------------------

async def distribute_data_via_http(data_type, data, available_nodes, max_retries=3):
    nodes = available_nodes.get(data_type, [])
    if not nodes:
        logging.warning(f"HTTP: No available node for data type '{data_type}'.")
        return

    to_remove = []

    for attempt in range(max_retries):
        if not nodes:
            logging.warning(f"HTTP: Lista de nós está vazia após falhas.")
            break

        node = nodes.pop(0)
        nodes.append(node)

        node_endpoint = node["node_endpoint"]

        if "consumption_kwh_per_hour" in data:
            consumption_field = "consumption_kwh_per_hour"
            value = data["consumption_kwh_per_hour"]
        elif "consumption_m3_per_hour" in data:
            consumption_field = "consumption_m3_per_hour"
            value = data["consumption_m3_per_hour"]
        else:
            logging.warning("HTTP: Nenhum campo de consumo encontrado.")
            return

        converted_data = {
            "type": "consumption",
            "id": data.get("id"),
            "street": data.get("street"),
            consumption_field: value,
            "date": data.get("date"),
            "time": data.get("time")
        }

        try:
            async with ClientSession() as session:
                async with session.post(node_endpoint, json=converted_data) as resp:
                    if resp.status == 200:
                        logging.info(f"HTTP: Data sent to {node['node_id']} at {node_endpoint}")
                        return
                    else:
                        logging.error(f"HTTP: Erro ao enviar para {node['node_id']} - Status {resp.status}")
        except Exception as e:
            logging.error(f"HTTP: Falha ao enviar para {node['node_id']} ({node_endpoint}): {e}")
            to_remove.append(node)

        logging.info(f"HTTP: Tentativa {attempt + 1} falhou. Tentando próximo...")

    # Remover nós que falharam
    for node in to_remove:
        if node in available_nodes.get(data_type, []):
            available_nodes[data_type].remove(node)
            logging.warning(f"[REMOVIDO] Nodo {node['node_id']} removido por falha de comunicação.")

    logging.error(f"HTTP: Falha total após {max_retries} tentativas para tipo '{data_type}'.")

# -----------------------------------
# Handlers dos endpoints principais
# -----------------------------------

async def handle_register_meter(request):
    try:
        data = await request.json()
        meter_id = data.get("id")
        street = data.get("street")
        meter_type = data.get("type")

        if not meter_id or not street or not meter_type:
            return web.json_response({"error": "Missing required fields"}, status=400)

        if register_meter(meter_id, street, meter_type):
            log_current_status()
            return web.json_response({"message": "Meter registered successfully"}, status=200)
        else:
            return web.json_response({"error": "Invalid meter type or already registered"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_receive_data(request, available_nodes):
    try:
        data = await request.json()
        logging.info(f"HTTP: Data received: {data}")
        start = time.time()

        data_type = determine_data_type(data)
        if not data_type:
            return web.json_response({"status": "Error: Data type not determined."}, status=400)

        await distribute_data_via_http(data_type, data, available_nodes)

        elapsed = time.time() - start
        logging.info(f"[MÉTRICA] Tempo de processamento no Load Balancer: {elapsed:.3f}s")

        return web.json_response({"status": "HTTP: Data successfully received"})

    except Exception as e:
        logging.error(f"HTTP Server Error: {e}")
        return web.json_response({"status": "HTTP Server Error"}, status=500)

async def handle_register_node(request, available_nodes):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        data_type = data.get("data_type")
        node_endpoint = data.get("node_endpoint")

        if not node_id or not data_type or not node_endpoint:
            return web.json_response({"status": "Error: Incomplete registration data."}, status=400)

        node_info = {
            "node_id": node_id,
            "node_endpoint": node_endpoint
        }
        if data_type not in available_nodes:
            available_nodes[data_type] = []
        available_nodes[data_type].append(node_info)
        logging.info(f"HTTP: Node registered: {node_info} for type {data_type}")

        return web.json_response({"status": "Node successfully registered."})
    except Exception as e:
        logging.error(f"Error in HTTP Node Registration: {e}")
        return web.json_response({"status": "Error in HTTP Node Registration"}, status=500)

# --------------------------------------
# Endpoints para LBs se registrarem
# --------------------------------------

async def handle_register_lb(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        ip = data.get("ip")
        http_port = data.get("http_port")

        if not node_id or not ip or not http_port:
            return web.json_response({"error": "Missing fields"}, status=400)

        register_load_balancer(node_id, ip, http_port)
        logging.info(f"[LB] Registrado: {node_id} ({ip}:{http_port})")
        return web.json_response({"status": "Load Balancer registered"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_unregister_lb(request):
    try:
        data = await request.json()
        node_id = data.get("node_id")

        if not node_id:
            return web.json_response({"error": "Missing node_id"}, status=400)

        if unregister_load_balancer(node_id):
            logging.info(f"[LB] Removido: {node_id}")
            return web.json_response({"status": "Load Balancer unregistered"})
        else:
            return web.json_response({"status": "Load Balancer not found"}, status=404)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# ----------------------
# Raiz e inicialização
# ----------------------

async def handle_root(request):
    return web.Response(text="Olá, sou o Load Balancer!", status=200)

async def start_http_server(port, available_nodes):
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_post("/receive_data", functools.partial(handle_receive_data, available_nodes=available_nodes))
    app.router.add_post("/register_node", functools.partial(handle_register_node, available_nodes=available_nodes))
    app.router.add_post("/receive_data/register_meter", handle_register_meter)
    app.router.add_post("/register_load_balancer", handle_register_lb)
    app.router.add_post("/unregister_load_balancer", handle_unregister_lb)

    logging.info(f"HTTP: Server running on port {port}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await asyncio.get_event_loop().create_future()
