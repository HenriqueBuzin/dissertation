# http_server.py

from registry import register_meter
from aiohttp import ClientSession
from aiohttp import web
import functools
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)

async def handle_register_meter(request):
    """Handles requests to register meters (HTTP)."""
    try:
        data = await request.json()
        meter_id = data.get("id")
        street = data.get("street")
        meter_type = data.get("type")

        if not meter_id or not street or not meter_type:
            return web.json_response({"error": "Missing required fields"}, status=400)

        if register_meter(meter_id, street, meter_type):
            return web.json_response({"message": "Meter registered successfully"}, status=200)
        else:
            return web.json_response({"error": "Invalid meter type"}, status=400)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Function to determine the data type based on the last consumption field
def determine_data_type(data):
    keys = list(data.keys())
    last_key = keys[-1] if keys else None
    if last_key and last_key.startswith('consumption_'):
        return last_key
    return None

# Function to distribute data via HTTP using round-robin
# Função para distribuir os dados via HTTP usando round-robin
async def distribute_data_via_http(data_type, data, available_nodes, max_retries=3):
    nodes = available_nodes.get(data_type, [])
    if not nodes:
        logging.warning(f"HTTP: No available node for data type '{data_type}'.")
        return

    for attempt in range(max_retries):
        # Seleciona o próximo nó de forma round-robin
        node = nodes.pop(0)
        nodes.append(node)  # Reinsere o nó no final da lista

        node_endpoint = node["node_endpoint"]

        # Converte o dado para o formato aceito pelos nós de névoa
        value = data.get("consumption_kwh_per_hour") or data.get("consumption_m3_per_hour")
        converted_data = {
            "type": "consumption",
            "id": data.get("id"),
            "street": data.get("street"),
            "value": value,
            "date": data.get("date"),
            "time": data.get("time")
        }

        try:
            async with ClientSession() as session:
                async with session.post(node_endpoint, json=converted_data) as resp:
                    if resp.status == 200:
                        logging.info(f"HTTP: Data sent to node {node['node_id']} at {node_endpoint}")
                        return
                    else:
                        logging.error(f"HTTP: Failed to send data to node {node['node_id']} at {node_endpoint}. Status: {resp.status}")
        except Exception as e:
            logging.error(f"HTTP: Error sending data to node {node['node_id']} at {node_endpoint}: {e}")

        logging.info(f"HTTP: Attempt {attempt + 1} of {max_retries} failed. Trying next node.")

    logging.error(f"HTTP: Failed to distribute data for type '{data_type}' after {max_retries} attempts.")

# Endpoint to receive data via HTTP
async def handle_receive_data(request, available_nodes):
    try:
        data = await request.json()

        # Determine the data type based on the last consumption field
        data_type = determine_data_type(data)

        if not data_type:
            logging.warning("HTTP: Data type could not be determined from consumption fields.")
            return web.json_response({"status": "Error: Data type not determined."}, status=400)

        logging.info(f"HTTP: Data received: {data}")

        # Distribute data to an appropriate node via HTTP
        await distribute_data_via_http(data_type, data, available_nodes)

        return web.json_response({"status": "HTTP: Data successfully received"})
    except Exception as e:
        logging.error(f"HTTP Server Error: {e}")
        return web.json_response({"status": "HTTP Server Error"}, status=500)

# Endpoint to register nodes via HTTP
async def handle_register_node(request, available_nodes):
    try:
        data = await request.json()
        node_id = data.get("node_id")
        data_type = data.get("data_type")
        node_endpoint = data.get("node_endpoint")  # e.g., "http://node_id:port/receive_data"

        if not node_id or not data_type or not node_endpoint:
            logging.warning("HTTP: Node registration received with incomplete data.")
            return web.json_response({"status": "Error: Incomplete registration data."}, status=400)

        # Add the node to the list of available nodes for the data type
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

# Start the HTTP server
async def start_http_server(port, available_nodes):
    app = web.Application()
    app.router.add_post("/receive_data", functools.partial(handle_receive_data, available_nodes=available_nodes))
    app.router.add_post("/register_node", functools.partial(handle_register_node, available_nodes=available_nodes))
    app.router.add_post("/receive_data/register_meter", handle_register_meter)
    
    logging.info(f"HTTP: Server running on port {port}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Keep the server running
    await asyncio.get_event_loop().create_future()
