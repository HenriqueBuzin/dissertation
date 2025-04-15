# coap_server.py

from aiocoap import Context, Message, resource, Code
from http_server import distribute_data_via_http
from registry import log_current_status
from registry import register_meter
import asyncio
import logging
import json
import time

# Configuração de log
logging.basicConfig(level=logging.INFO)

# --------------------------------------------------
# Função para identificar o tipo de dado recebido
# --------------------------------------------------

def determine_data_type(data):
    keys = list(data.keys())
    last_key = keys[-1] if keys else None
    if last_key and last_key.startswith('consumption_'):
        return last_key
    return None

# --------------------------------------------------
# Recurso CoAP para /receive_data
# --------------------------------------------------

class CoAPReceiveDataResource(resource.Resource):
    def __init__(self, available_nodes):
        super().__init__()
        self.available_nodes = available_nodes

    async def render_post(self, request):
        try:
            start = time.time()
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            logging.info(f"CoAP: Received data: {data}")

            data_type = determine_data_type(data)

            if not data_type:
                logging.warning("CoAP: Data type could not be determined.")
                return Message(payload=b"Error: Data type not determined.", code=Code.BAD_REQUEST)

            await distribute_data_via_http(data_type, data, self.available_nodes)

            elapsed = time.time() - start
            logging.info(f"[MÉTRICA] Tempo de processamento no Load Balancer: {elapsed:.3f}s")

            return Message(payload=b"CoAP: Data successfully received", code=Code.CONTENT)

        except Exception as e:
            logging.error(f"CoAP Server Error: {e}")
            return Message(payload=b"CoAP Server Error", code=Code.INTERNAL_SERVER_ERROR)

# --------------------------------------------------
# Recurso CoAP para /register_meter
# --------------------------------------------------

class CoAPRegisterMeterResource(resource.Resource):
    async def render_post(self, request):
        try:
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            meter_id = data.get("id")
            street = data.get("street")
            meter_type = data.get("type")

            if not meter_id or not street or not meter_type:
                return Message(payload=b"Error: Missing required fields.", code=Code.BAD_REQUEST)

            if register_meter(meter_id, street, meter_type):
                log_current_status()
                return Message(payload=b"CoAP: Meter successfully registered", code=Code.CONTENT)
            else:
                return Message(payload=b"Error: Invalid meter type or meter already registered.", code=Code.BAD_REQUEST)

        except Exception as e:
            logging.error(f"CoAP RegisterMeter Error: {e}")
            return Message(payload=b"Error in CoAP meter registration", code=Code.INTERNAL_SERVER_ERROR)

# --------------------------------------------------
# Inicialização do servidor CoAP
# --------------------------------------------------

async def start_coap_server(port, available_nodes):
    try:
        root = resource.Site()
        root.add_resource(("receive_data",), CoAPReceiveDataResource(available_nodes))
        root.add_resource(("register_meter",), CoAPRegisterMeterResource())

        logging.info(f"CoAP: Server running on port {port}...")
        await Context.create_server_context(root, bind=("0.0.0.0", port))

        await asyncio.get_event_loop().create_future()
    except Exception as e:
        logging.error(f"Error starting CoAP server: {e}")
