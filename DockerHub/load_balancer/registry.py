# registry.py

import logging

# Structures to store records
registered_meters = {
    "energy": [],  # Energy meters
    "water": []    # Water meters
}

available_nodes = {
    "consumption_m3_per_hour": [],  # Water nodes
    "consumption_kwh_per_hour": []  # Energy nodes
}

def register_meter(meter_id, street, meter_type):
    """Registers a meter in the system, checking for duplicates."""
    
    if meter_type not in registered_meters:
        logging.warning(f"Invalid meter type: {meter_type}")
        return False

    # Check if the meter is already registered
    for meter in registered_meters[meter_type]:
        if meter["id"] == meter_id:
            logging.warning(f"Meter {meter_id} is already registered.")
            return False

    registered_meters[meter_type].append({"id": meter_id, "street": street})
    logging.info(f"Meter registered: ID={meter_id}, Street={street}, Type={meter_type}")
    return True

def register_node(node_id, node_type, node_endpoint):
    """Registers a node in the system, checking for duplicates."""
    
    if node_type not in available_nodes:
        logging.warning(f"Invalid node type: {node_type}")
        return False

    # Check if the node is already registered
    for node in available_nodes[node_type]:
        if node["node_id"] == node_id:
            logging.warning(f"Node {node_id} is already registered.")
            return False

    available_nodes[node_type].append({"node_id": node_id, "endpoint": node_endpoint})
    logging.info(f"Node registered: ID={node_id}, Type={node_type}, Endpoint={node_endpoint}")
    return True

def get_registered_meters():
    """Returns the registered meters."""
    return registered_meters

def get_available_nodes():
    """Returns the registered nodes."""
    return available_nodes
