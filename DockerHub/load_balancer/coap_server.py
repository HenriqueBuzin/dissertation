# coap_server.py

import asyncio
from aiocoap import Context, Message, resource, Code
import logging

# Import the HTTP distribution function
from http_server import distribute_data_via_http

# Configure logging
logging.basicConfig(level=logging.INFO)

# Resource to handle /receive_data on CoAP server
class CoAPReceiveDataResource(resource.Resource):
    def __init__(self, available_nodes):
        super().__init__()
        self.available_nodes = available_nodes

    async def render_post(self, request):
        try:
            # Decode the received payload
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)
            data_type = data.get("type")

            if not data_type:
                logging.warning("CoAP: Data received without specified type.")
                return Message(payload=b"Error: Data type not specified.", code=Code.BAD_REQUEST)

            logging.info(f"CoAP: Data received: {data}")

            # Delegate data distribution via HTTP
            await distribute_data_via_http(data_type, data, self.available_nodes)

            # Return success response
            return Message(payload=b"CoAP: Data received successfully", code=Code.CONTENT)
        except Exception as e:
            logging.error(f"CoAP Server Error: {e}")
            # Return internal server error response
            return Message(payload=b"CoAP Server Error", code=Code.INTERNAL_SERVER_ERROR)

# Start the CoAP server
async def start_coap_server(port, available_nodes):
    try:
        root = resource.Site()
        receive_data_resource = CoAPReceiveDataResource(available_nodes)
        root.add_resource(("receive_data",), receive_data_resource)

        # Configure the CoAP server to listen on the specified port
        logging.info(f"CoAP: Server running on port {port}...")
        await Context.create_server_context(root, bind=("0.0.0.0", port))

        # Keep the server running
        await asyncio.get_event_loop().create_future()
    except Exception as e:
        logging.error(f"Error starting CoAP server: {e}")
