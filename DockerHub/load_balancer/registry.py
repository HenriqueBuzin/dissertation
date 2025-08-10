import logging
import time

# ---------------------------------------
# Armazenamento em memória
# ---------------------------------------
registered_meters = {
    "energy": [],  # Medidores de energia
    "water": []    # Medidores de água
}
available_nodes = {
    "consumption_m3_per_hour": [],      # Nós para água
    "consumption_kwh_per_hour": []      # Nós para energia
}
known_load_balancers = {}  # node_id -> { ip, http_port, last_seen }

# ---------------------------------------
# Registro de medidores
# ---------------------------------------
def register_meter(meter_id, street, meter_type):
    if meter_type not in registered_meters:
        logging.warning(f"Invalid meter type: {meter_type}")
        return False
    for m in registered_meters[meter_type]:
        if m["id"] == meter_id:
            logging.warning(f"Meter {meter_id} already registered.")
            return False
    registered_meters[meter_type].append({"id": meter_id, "street": street})
    logging.info(f"[REGISTRAR MEDIDOR] ID={meter_id} | street={street} | type={meter_type}")
    return True

# **Nova função** para expor os medidores registrados
def get_registered_meters():
    """
    Retorna o dicionário com todos os medidores registrados,
    agrupados por tipo ("energy", "water").
    """
    return registered_meters

# ---------------------------------------
# Registro de fog‑nodes
# ---------------------------------------
def register_node(node_id, node_type, node_endpoint):
    if node_type not in available_nodes:
        logging.warning(f"Invalid node type: {node_type}")
        return False
    for n in available_nodes[node_type]:
        if n["node_id"] == node_id:
            logging.warning(f"Node {node_id} already registered.")
            return False
    available_nodes[node_type].append({
        "node_id": node_id,
        "node_endpoint": node_endpoint
    })
    logging.info(f"[REGISTRAR NÓ] ID={node_id} | type={node_type} | endpoint={node_endpoint}")
    return True

# ---------------------------------------
# Registro de Load Balancers
# ---------------------------------------
def register_load_balancer(node_id, ip, http_port):
    known_load_balancers[node_id] = {
        "ip": ip,
        "http_port": http_port,
        "last_seen": time.time()
    }
    logging.info(f"[REGISTRAR LB] ID={node_id} | {ip}:{http_port}")
    return True

def unregister_load_balancer(node_id):
    if node_id in known_load_balancers:
        del known_load_balancers[node_id]
        logging.info(f"[REMOVER LB] ID={node_id}")
        return True
    return False

def get_load_balancers():
    return known_load_balancers

def get_available_nodes():
    return available_nodes

def log_current_status():
    e = len(registered_meters["energy"])
    w = len(registered_meters["water"])
    ke = len(available_nodes["consumption_kwh_per_hour"])
    km = len(available_nodes["consumption_m3_per_hour"])
    logging.info(f"[STATUS] Medidores → energia={e} | água={w}")
    logging.info(f"[STATUS] Fog‑nodes → energia={ke} | água={km}")
