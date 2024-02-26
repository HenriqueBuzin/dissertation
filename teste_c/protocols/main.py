import asyncio
import json
import threading
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiocoap.resource import Resource, Site
import aiocoap

ws_url = 'ws://127.0.0.1:8765/'
graphql_mutation = '''
mutation sendData($data: JSON!) {
    processData(input: $data) {
        success
        message
    }
}
'''

message_queue = []

async def send_data_websocket():
    while True:
        if message_queue:
            try:
                async with websockets.connect(ws_url) as ws:
                    while message_queue:
                        data = message_queue.pop(0)
                        mutation = graphql_mutation.replace('$data', json.dumps(data))
                        await ws.send(mutation)
                        response = await ws.recv()
                        print(f"Websocket: Dados enviados com sucesso: {data} \nResposta: {response}")
            except Exception as e:
                print(f"Websocket: Erro ao enviar WebSocket: {e}. Tentando novamente em 1 segundo...")
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        message = json.loads(post_data.decode())
        print(f"HTTP: Mensagem HTTP recebida: {message}")
        message_queue.append(message)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"HTTP: Message received")

def run_http_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print('HTTP: Servidor HTTP rodando na porta 8000...')
    httpd.serve_forever()

class CoAPResource(Resource):
    async def render_post(self, request):
        payload = request.payload.decode('utf8')
        print(f'CoAP: Mensagem CoAP recebida: {payload}')
        message = json.loads(payload)
        message_queue.append(message)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Received")

async def start_coap_server():
    root = Site()
    root.add_resource(['coap'], CoAPResource())
    return await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))

async def main():
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    coap_context = await start_coap_server()
    websocket_task = asyncio.create_task(send_data_websocket())

    try:
        await websocket_task
    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário. Encerrando o script.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerramento finalizado pelo usuário.")
