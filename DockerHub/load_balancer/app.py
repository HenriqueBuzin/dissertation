from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def status():
    return jsonify({"status": "Load Balancer is running"}), 200

@app.route('/receive_data', methods=['POST'])
def receive_data():
    data = request.json
    print(f"Dados recebidos: {data}")
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    port = int(os.getenv("LOAD_BALANCER_PORT", 5000))
    print(f"Iniciando Load Balancer na porta {port}")
    app.run(debug=True, port=port)