from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests

def handle_POST(request):
    content_length = int(request.headers['Content-Length'])
    body = request.rfile.read(content_length)
    data = json.loads(body)

    print(f"Dados recebidos: {data}")

    # Enviar dados para o servidor GraphQL
    graphql_url = 'http://localhost:5001/graphql'  # URL do seu servidor GraphQL
    graphql_query = """
        mutation {
            addData(date: "%s", time: "%s", consumption: %s) {
                date
                time
                consumption
            }
        }
    """ % (data['Date'], data['Time'], data['Consumption_kWh_per_minute'])
    
    try:
        response = requests.post(graphql_url, json={'query': graphql_query})
        print("Dados enviados para o servidor GraphQL:", response.text)
    except requests.exceptions.RequestException as e:
        print("Falha ao enviar para o servidor GraphQL:", e)

    request.send_response(200)
    request.end_headers()
    response = bytes(json.dumps({"message": "Dados recebidos e enviados com sucesso!"}), "utf-8")
    request.wfile.write(response)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        handle_POST(self)

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
    print(f"Servidor iniciado em http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário. Encerrando o servidor.")
        server.server_close()
