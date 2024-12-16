from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import asyncio
from protocols.sftp_handler import handle_sftp_details_and_send

def run_http_server(protocol_layer):
    class CustomHTTPRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.protocol_layer = protocol_layer
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
                    asyncio.run(handle_sftp_details_and_send(message))
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
