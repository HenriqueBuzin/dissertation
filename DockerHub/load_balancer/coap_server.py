# coap_server.py

import asyncio
from aiocoap import Context, Message, resource, Code
import logging
import json

# Importa funções para distribuir dados e registrar medidores
from http_server import distribute_data_via_http
from registry import register_meter

# Configuração do logging
logging.basicConfig(level=logging.INFO)

# Função para determinar o tipo de dado com base no último campo de consumo
def determine_data_type(data):
    keys = list(data.keys())
    last_key = keys[-1] if keys else None
    if last_key and last_key.startswith('consumption_'):
        return last_key
    return None

# Recurso CoAP para receber dados em /receive_data
class CoAPReceiveDataResource(resource.Resource):
    def __init__(self, available_nodes):
        super().__init__()
        self.available_nodes = available_nodes

    async def render_post(self, request):
        try:
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            # Determinar o tipo de dado baseado nos campos de consumo
            data_type = determine_data_type(data)

            if not data_type:
                logging.warning("CoAP: Dados recebidos sem tipo determinado.")
                return Message(payload="Erro: Tipo de dado não determinado.".encode("utf-8"), code=Code.BAD_REQUEST)

            logging.info(f"CoAP: Dados recebidos: {data}")

            # Distribuir os dados via HTTP
            await distribute_data_via_http(data_type, data, self.available_nodes)

            return Message(payload="CoAP: Dados recebidos com sucesso".encode("utf-8"), code=Code.CONTENT)
        except Exception as e:
            logging.error(f"Erro no Servidor CoAP: {e}")
            return Message(payload="Erro no Servidor CoAP".encode("utf-8"), code=Code.INTERNAL_SERVER_ERROR)

# Recurso CoAP para registrar medidores em /register_meter
class CoAPRegisterMeterResource(resource.Resource):
    async def render_post(self, request):
        try:
            payload = request.payload.decode("utf-8")
            data = json.loads(payload)

            meter_id = data.get("id")
            street = data.get("street")
            meter_type = data.get("type")

            if not meter_id or not street or not meter_type:
                return Message(payload="Erro: Campos obrigatórios ausentes.".encode("utf-8"), code=Code.BAD_REQUEST)

            # Registrar o medidor usando a função do `registry.py`
            if register_meter(meter_id, street, meter_type):
                logging.info(f"CoAP: Medidor {meter_id} ({meter_type}) registrado com sucesso.")
                return Message(payload="CoAP: Medidor registrado com sucesso".encode("utf-8"), code=Code.CONTENT)
            else:
                return Message(payload="Erro: Tipo de medidor inválido ou já registrado.".encode("utf-8"), code=Code.BAD_REQUEST)

        except Exception as e:
            logging.error(f"Erro ao registrar medidor via CoAP: {e}")
            return Message(payload="Erro no registro de medidor CoAP".encode("utf-8"), code=Code.INTERNAL_SERVER_ERROR)

# Start the CoAP server
async def start_coap_server(port, available_nodes):
    try:
        root = resource.Site()
        root.add_resource(("receive_data",), CoAPReceiveDataResource(available_nodes))
        root.add_resource(("register_meter",), CoAPRegisterMeterResource())

        logging.info(f"CoAP: Server running on port {port}...")
        await Context.create_server_context(root, bind=("0.0.0.0", port))

        # Mantém o servidor rodando
        await asyncio.get_event_loop().create_future()
    except Exception as e:
        logging.error(f"Erro ao iniciar o servidor CoAP: {e}")
