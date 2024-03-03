import asyncio
import json
import threading
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiocoap.resource import Resource, Site
import aiocoap.resource as resource
import aiocoap

ws_url = 'ws://127.0.0.1:8765/'
message_queue = []

async def send_data_websocket():
    while True:
        if message_queue:
            try:
                async with websockets.connect(ws_url) as ws:
                    while message_queue:
                        data = message_queue.pop(0)
                        await ws.send(json.dumps(data))
                        response = await ws.recv()
                        print(f"Websocket: Dados enviados com sucesso: {json.dumps(data)} \nResposta: {response}")
            except Exception as e:
                print(f"Websocket: Erro ao enviar dados: {e}. Tentando novamente em 1 segundo...")
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)

def handle_http_post(self):
    content_length = int(self.headers['Content-Length'])
    post_data = self.rfile.read(content_length)
    message = json.loads(post_data.decode())
    print(f"HTTP: Mensagem HTTP recebida: {message}")
    message_queue.append(message)
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"HTTP: Message received")

def create_custom_http_handler():
    attrs = {'do_POST': handle_http_post}
    return type('CustomHTTPRequestHandler', (BaseHTTPRequestHandler,), attrs)

def run_http_server():
    port = 8000
    server_address = ('', port)
    handler_class = create_custom_http_handler()
    httpd = HTTPServer(server_address, handler_class)
    print(f'HTTP: Servidor HTTP rodando na porta {port}...')
    httpd.serve_forever()

# Função que lida com POST requests para CoAP
async def handle_coap_post(request):
    payload = request.payload.decode('utf8')
    message = json.loads(payload)
    print(f'CoAP: Mensagem CoAP recebida: {message}')
    return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Received")

def make_coap_resource(handle_post_function):
    class DynamicCoAPResource(resource.Resource):
        async def render_post(self, request):
            return await handle_post_function(request)
    return DynamicCoAPResource

async def start_coap_server():
    root = resource.Site()
    CoAPResource = make_coap_resource(handle_coap_post)
    root.add_resource(['coap'], CoAPResource())
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))

async def main():
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    await start_coap_server()
    await send_data_websocket()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCamada de protocolos encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução da camada de protocolos: {e}")
    finally:
        print("Camada de protocolos encerrada com sucesso.")
