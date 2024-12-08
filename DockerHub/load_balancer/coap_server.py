import asyncio
from aiocoap import Context, Message, resource, Code
import logging

# Configuração de log
logging.basicConfig(level=logging.INFO)

# Recurso para lidar com /receive_data no servidor CoAP
class CoAPServerResource(resource.Resource):
    async def render_post(self, request):
        try:
            # Decodifica o payload recebido
            payload = request.payload.decode("utf-8")
            logging.info(f"CoAP: Dados recebidos: {payload}")
            
            # Retorna resposta de sucesso
            return Message(payload=b"CoAP: Dados recebidos com sucesso", code=Code.CONTENT)
        except Exception as e:
            logging.error(f"Erro no servidor CoAP: {e}")
            
            # Retorna resposta de erro interno
            return Message(payload=b"Erro no servidor CoAP", code=Code.INTERNAL_SERVER_ERROR)

# Inicia o servidor CoAP
async def start_coap_server(port):
    try:
        root = resource.Site()
        root.add_resource(("receive_data",), CoAPServerResource())
        
        # Configura o servidor CoAP para escutar na porta especificada
        logging.info(f"CoAP: Servidor rodando na porta {port}...")
        await Context.create_server_context(root, bind=("0.0.0.0", port))
        
        # Mantém o servidor rodando
        await asyncio.get_event_loop().create_future()
    except Exception as e:
        logging.error(f"Erro ao iniciar o servidor CoAP: {e}")
