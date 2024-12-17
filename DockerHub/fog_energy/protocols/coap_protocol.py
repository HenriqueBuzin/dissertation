import aiocoap.resource as resource
import aiocoap
import json

class CoAPServerResource(resource.Resource):
    def __init__(self, protocol_layer):
        super().__init__()
        self.protocol_layer = protocol_layer

    async def render_post(self, request):
        print("Recebendo mensagem CoAP...", flush=True)
        payload = request.payload.decode('utf8')
        print(f"Payload CoAP: {payload}", flush=True)
        message = json.loads(payload)
        self.protocol_layer.save_message(message)
        print("Mensagem CoAP salva com sucesso.", flush=True)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Received")

async def start_coap_server(protocol_layer):
    root = resource.Site()
    coap_resource = CoAPServerResource(protocol_layer)
    root.add_resource(['coap'], coap_resource)
    port = 5683
    print(f'CoAP: Servidor CoAP rodando na porta {port}...', flush=True)
    await aiocoap.Context.create_server_context(root, bind=('0.0.0.0', port))
