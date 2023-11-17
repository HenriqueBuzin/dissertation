from http.server import HTTPServer, BaseHTTPRequestHandler
import json

def handle_POST(request):
    content_length = int(request.headers['Content-Length'])
    body = request.rfile.read(content_length)
    data = json.loads(body)

    print(f"Dados recebidos: {data}")

    request.send_response(200)
    request.end_headers()
    response = bytes(json.dumps({"message": "Dados recebidos com sucesso!"}), "utf-8")
    request.wfile.write(response)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        handle_POST(self)

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
    print(f"Servidor iniciado em http://localhost:{port}")
    server.serve_forever()
