import aiocoap.resource as resource
import aiocoap
import json

class CoAPServerResource(resource.Resource):
    def __init__(self, protocol_layer):
        super().__init__()
        self.protocol_layer = protocol_layer

    async def render_post(self, request):
        print("Recebendo mensagem CoAP...")
        payload = request.payload.decode('utf8')
        print(f"Payload CoAP: {payload}")
        message = json.loads(payload)
        self.protocol_layer.save_message(message)
        print("Mensagem CoAP salva com sucesso.")
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Received")

async def start_coap_server(protocol_layer):
    root = resource.Site()
    coap_resource = CoAPServerResource(protocol_layer)
    root.add_resource(['coap'], coap_resource)
    port = 5683
    print(f'CoAP: Servidor CoAP rodando na porta {port}...')
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', port))
