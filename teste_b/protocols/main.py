import asyncio
import json
import os
import threading
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
import aiocoap.resource as resource
import aiocoap
from pymongo import MongoClient
import redis
from dotenv import load_dotenv
import paramiko
import base64
import aiofiles

class ProtocolLayer:
    def __init__(self):
        self.load_env()
        self.redis_client = redis.Redis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.PROTOCOLS_REDIS_DB, decode_responses=True)
        self.mongo_client = MongoClient(self.MONGO_URI)
        self.mongo_db = self.mongo_client[self.MONGO_DB]
        self.mongo_collection = self.mongo_db["protocols_data"]
        self.ws_url = 'ws://processing:8765/'

    def load_env(self):
        base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        dotenv_path = os.path.join(base_dir, '..', '.env')
        load_dotenv(dotenv_path=dotenv_path)
        self.REDIS_HOST = os.getenv("REDIS_HOST", "redis")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        self.PROTOCOLS_REDIS_DB = int(os.getenv("PROTOCOLS_REDIS_DB", 0))
        self.MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
        self.MONGO_PORT = os.getenv("MONGO_PORT", "27017")
        self.MONGO_DB = os.getenv("MONGO_DB", "fog")
        self.MONGO_USER = os.getenv("MONGO_USER")
        self.MONGO_PASS = os.getenv("MONGO_PASS")
        self.MONGO_URI = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASS}@{self.MONGO_HOST}:{self.MONGO_PORT}/"
        self.PROTOCOLS_PERSIST = int(os.getenv("PROTOCOLS_PERSIST", 1))

    async def send_data_websocket(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    await self.send_messages(ws)
            except Exception as e:
                print(f"WebSocket: Erro ao conectar ou enviar dados: {e}. Tentando novamente em 1 segundo...")
                await asyncio.sleep(1)

    async def send_messages(self, ws):
        if self.PROTOCOLS_PERSIST == 1:
            messages = list(self.mongo_collection.find({}))
            for message in messages:
                await ws.send(json.dumps(message, default=str))
                self.mongo_collection.delete_one({"_id": message["_id"]})
        else:
            while self.redis_client.llen("protocols_messages") > 0:
                message = self.redis_client.rpop("protocols_messages")
                await ws.send(message)
        await asyncio.sleep(1)

    def save_message(self, message):
        if self.PROTOCOLS_PERSIST == 1:
            self.mongo_collection.insert_one(message)
        else:
            self.redis_client.lpush("protocols_messages", json.dumps(message))

    async def handle_sftp_details_and_send(self, message):
        file_content = base64.b64decode(message['file']).decode('utf-8')

        temp_file_path = "temp_file.csv"
        async with aiofiles.open(temp_file_path, mode='w', encoding='utf-8') as temp_file:
            await temp_file.write(file_content)

        sftp_details = {
            'sftp_host': message['sftp_host'],
            'sftp_port': message['sftp_port'],
            'sftp_username': message['sftp_username'],
            'sftp_password': message['sftp_password'],
            'remote_path': message['remote_path']
        }

        await self.send_via_sftp(sftp_details, temp_file_path)

    async def send_via_sftp(self, sftp_details, file_path):
        try:
            transport = paramiko.Transport((sftp_details['sftp_host'], sftp_details['sftp_port']))
            transport.connect(username=sftp_details['sftp_username'], password=sftp_details['sftp_password'])
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            sftp.put(file_path, sftp_details['remote_path'])
            print(f"Arquivo {file_path} enviado com sucesso para {sftp_details['remote_path']}.")

            sftp.close()
            transport.close()

            try:
                os.remove(file_path)
                print(f"Arquivo temporário {file_path} removido com sucesso.")
            except Exception as e:
                print(f"Erro ao remover o arquivo temporário {file_path}: {e}")

        except Exception as e:
            print(f"Erro ao enviar arquivo via FTP: {e}")

def run_http_server(protocol_layer):
    class CustomHTTPRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.protocol_layer = ProtocolLayer()
            super().__init__(*args, **kwargs)
            
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                message = json.loads(post_data.decode())

                print("Recebendo mensagem HTTP...")
                print(f"Dados HTTP recebidos: {message}")

                message_type = message.get('type')
                if message_type == 'consumption':
                    print("Processando dados de consumo...")
                    self.protocol_layer.save_message(message)
                    response_content = b"HTTP: Consumption data received"
                elif message_type == 'ftp':
                    print("Processando detalhes do FTP...")
                    asyncio.run(self.protocol_layer.handle_sftp_details_and_send(message))
                    response_content = b"HTTP: FTP details received"
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"HTTP: Unknown message type")
                    return

                self.send_response(200)
                self.end_headers()
                self.wfile.write(response_content)

            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"HTTP: Error decoding JSON")

    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
    print(f'HTTP: Servidor HTTP rodando na porta {port}...')
    httpd.serve_forever()

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
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))

async def main():
    protocol_layer = ProtocolLayer()
    http_thread = threading.Thread(target=lambda: run_http_server(protocol_layer), daemon=True)
    http_thread.start()
    await start_coap_server(protocol_layer)
    await protocol_layer.send_data_websocket()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCamada de Protocolos encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução da Camada de Protocolos: {e}")
    finally:
        print("Camada de Protocolos encerrada com sucesso.")
