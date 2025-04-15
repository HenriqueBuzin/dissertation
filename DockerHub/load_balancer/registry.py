# registry.py

import logging
import time

# ---------------------------------------
# Estrutura de armazenamento
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
# Funções para medidores
# ---------------------------------------

def register_meter(meter_id, street, meter_type):
    if meter_type not in registered_meters:
        logging.warning(f"Invalid meter type: {meter_type}")
        return False

    for meter in registered_meters[meter_type]:
        if meter["id"] == meter_id:
            logging.warning(f"Meter {meter_id} already registered.")
            return False

    registered_meters[meter_type].append({"id": meter_id, "street": street})
    logging.info(f"Meter registered: ID={meter_id}, Street={street}, Type={meter_type}")
    return True

def get_registered_meters():
    return registered_meters

# ---------------------------------------
# Funções para nós de névoa
# ---------------------------------------

def register_node(node_id, node_type, node_endpoint):
    if node_type not in available_nodes:
        logging.warning(f"Invalid node type: {node_type}")
        return False

    for node in available_nodes[node_type]:
        if node["node_id"] == node_id:
            logging.warning(f"Node {node_id} already registered.")
            return False

    available_nodes[node_type].append({
        "node_id": node_id,
        "node_endpoint": node_endpoint
    })
    logging.info(f"Node registered: ID={node_id}, Type={node_type}, Endpoint={node_endpoint}")
    return True

def get_available_nodes():
    return available_nodes

# ---------------------------------------
# Funções para Load Balancers
# ---------------------------------------

def register_load_balancer(node_id, ip, http_port):
    known_load_balancers[node_id] = {
        "ip": ip,
        "http_port": http_port,
        "last_seen": time.time()
    }
    logging.info(f"Load Balancer registered: {node_id} ({ip}:{http_port})")
    return True

def unregister_load_balancer(node_id):
    if node_id in known_load_balancers:
        del known_load_balancers[node_id]
        logging.info(f"Load Balancer unregistered: {node_id}")
        return True
    return False

def get_load_balancers():
    return known_load_balancers

# ---------------------------------------
# Funções de status
# ---------------------------------------

def gather_stats():
    registered = get_registered_meters()
    nodes = get_available_nodes()
    return {
        "registered_meters": len(registered.get("energy", [])) + len(registered.get("water", [])),
        "energy_meters": len(registered.get("energy", [])),
        "water_meters": len(registered.get("water", [])),
        "fog_nodes_energy": len(nodes.get("consumption_kwh_per_hour", [])),
        "fog_nodes_water": len(nodes.get("consumption_m3_per_hour", [])),
    }

def log_current_status():
    stats = gather_stats()
    logging.info(
        "[STATUS] Medidores -> "
        f"ENERGIA={stats['energy_meters']} | "
        f"ÁGUA={stats['water_meters']}"
    )
    logging.info(
        "[STATUS] FogNodes -> "
        f"ENERGIA={stats['fog_nodes_energy']} | "
        f"ÁGUA={stats['fog_nodes_water']}"
    )
