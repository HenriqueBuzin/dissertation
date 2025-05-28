# coap_server.py

import asyncio
import json
import time
import logging
from aiocoap import Context, Message, resource, Code
from data_distributor import distribute_data
from registry import log_current_status, register_meter

logging.basicConfig(level=logging.INFO)

def determine_data_type(data):
    return next((k for k in data if k.startswith('consumption_')), None)

class CoAPReceiveDataResource(resource.Resource):
    async def render_post(self, request):
        try:
            start = time.time()
            data = json.loads(request.payload.decode('utf-8'))
            logging.info(f"[CoAP ← RECEIVE] {data}")

            if not determine_data_type(data):
                return Message("Tipo não determinado".encode("utf-8"), Code.BAD_REQUEST)

            await distribute_data(data)
            logging.info(f"[MÉTRICA CoAP] {time.time()-start:.3f}s")
            return Message(b"Recebido com sucesso", Code.CONTENT)
        except Exception as e:
            logging.error(f"CoAP Error: {e}")
            return Message(b"Erro interno CoAP", Code.INTERNAL_SERVER_ERROR)

class CoAPRegisterMeterResource(resource.Resource):
    async def render_post(self, request):
        try:
            d = json.loads(request.payload.decode('utf-8'))
            if not all(k in d for k in ("id","street","type")):
                return Message(b"Campos faltando", Code.BAD_REQUEST)
            if register_meter(d["id"], d["street"], d["type"]):
                log_current_status()
                return Message(b"Medidor registrado", Code.CONTENT)
            else:
                return Message("Registro inválido ou duplicado".encode("utf-8"), Code.BAD_REQUEST)
        except Exception as e:
            logging.error(f"CoAP RegisterMeter Error: {e}")
            return Message(b"Erro interno registro", Code.INTERNAL_SERVER_ERROR)

async def start_coap_server(port):
    root = resource.Site()
    root.add_resource(('receive_data',), CoAPReceiveDataResource())
    root.add_resource(('register_meter',), CoAPRegisterMeterResource())
    logging.info(f"CoAP rodando na porta {port}")
    await Context.create_server_context(root, bind=('0.0.0.0', port))
    await asyncio.get_event_loop().create_future()
