# coap_server.py

import asyncio
from aiocoap import Context, Message, resource, Code
import logging
import json

# Import functions to distribute data and register meters
from http_server import distribute_data_via_http
from registry import register_meter

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Function to determine the data type based on the last consumption field
def determine_data_type(data):
    keys = list(data.keys())
    last_key = keys[-1] if keys else None
    if last_key and last_key.startswith('consumption_'):
        return last_key
    return None

# CoAP resource to receive data at /receive_data
class CoAPReceiveDataResource(resource.Resource):
    def __init__(self, available_nodes):
        super().__init__()
        self.available_nodes = available_nodes

    async def render_post(self, request):
        try:
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            # Determine the data type based on consumption fields
            data_type = determine_data_type(data)

            if not data_type:
                logging.warning("CoAP: Received data without a determined type.")
                return Message(payload="Error: Data type not determined.".encode("utf-8"), code=Code.BAD_REQUEST)

            logging.info(f"CoAP: Received data: {data}")

            # Distribute data via HTTP
            await distribute_data_via_http(data_type, data, self.available_nodes)

            return Message(payload="CoAP: Data successfully received".encode("utf-8"), code=Code.CONTENT)
        except Exception as e:
            logging.error(f"CoAP Server Error: {e}")
            return Message(payload="CoAP Server Error".encode("utf-8"), code=Code.INTERNAL_SERVER_ERROR)

# CoAP resource to register meters at /register_meter
class CoAPRegisterMeterResource(resource.Resource):
    async def render_post(self, request):
        try:
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            # Pega {id, street, type}
            meter_id = data.get("id")
            street = data.get("street")
            meter_type = data.get("type")

            if not meter_id or not street or not meter_type:
                return Message(payload=b"Error: Missing required fields.", code=Code.BAD_REQUEST)

            # Chama register_meter do registry.py
            if register_meter(meter_id, street, meter_type):
                return Message(payload=b"CoAP: Meter successfully registered", code=Code.CONTENT)
            else:
                return Message(payload=b"Error: Invalid meter type or meter already registered.", code=Code.BAD_REQUEST)

        except Exception as e:
            logging.error(f"CoAP RegisterMeter Error: {e}")
            return Message(payload=b"Error in CoAP meter registration", code=Code.INTERNAL_SERVER_ERROR)

# Start the CoAP server
async def start_coap_server(port, available_nodes):
    try:
        root = resource.Site()
        root.add_resource(("receive_data",), CoAPReceiveDataResource(available_nodes))
        root.add_resource(("register_meter",), CoAPRegisterMeterResource())

        logging.info(f"CoAP: Server running on port {port}...")
        await Context.create_server_context(root, bind=("0.0.0.0", port))

        # Keep the server running
        await asyncio.get_event_loop().create_future()
    except Exception as e:
        logging.error(f"Error starting CoAP server: {e}")
