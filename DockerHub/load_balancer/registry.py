# registry.py

import logging

# Estruturas para armazenar os registros
registered_meters = {
    "energy": [],  # Medidores de energia
    "water": []    # Medidores de água
}

available_nodes = {
    "consumption_m3_per_hour": [],  # Nodos de água
    "consumption_kwh_per_hour": []  # Nodos de energia
}

def register_meter(meter_id, street, meter_type):

    """Registra um medidor no sistema, verificando duplicatas."""
    
    if meter_type not in registered_meters:
        logging.warning(f"Tipo de medidor inválido: {meter_type}")
        return False

    # Verifica se o medidor já está registrado
    for meter in registered_meters[meter_type]:
        if meter["id"] == meter_id:
            logging.warning(f"Medidor {meter_id} já está registrado.")
            return False

    registered_meters[meter_type].append({"id": meter_id, "street": street})
    logging.info(f"Medidor registrado: ID={meter_id}, Rua={street}, Tipo={meter_type}")
    return True

def register_node(node_id, node_type, node_endpoint):

    """Registra um nodo no sistema, verificando duplicatas."""
    
    if node_type not in available_nodes:
        logging.warning(f"Tipo de nodo inválido: {node_type}")
        return False

    # Verifica se o nó já está registrado
    for node in available_nodes[node_type]:
        if node["node_id"] == node_id:
            logging.warning(f"Nó {node_id} já está registrado.")
            return False

    available_nodes[node_type].append({"node_id": node_id, "endpoint": node_endpoint})
    logging.info(f"Nodo registrado: ID={node_id}, Tipo={node_type}, Endpoint={node_endpoint}")
    return True

def get_registered_meters():

    """Retorna os medidores registrados."""

    return registered_meters

def get_available_nodes():

    """Retorna os nodos registrados."""

    return available_nodes
