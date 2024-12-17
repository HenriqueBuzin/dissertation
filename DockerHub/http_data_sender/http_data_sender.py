import csv
import json
import requests
import time
import os
import sys

HTTP_SERVER_URL = os.getenv('HTTP_SERVER_URL')
SEND_INTERVAL = int(os.getenv('SEND_INTERVAL', 1))
CSV_URL = os.getenv('CSV_URL')
INSTANCE_DATA = os.getenv('INSTANCE_DATA')

print("Variáveis de Ambiente Recebidas:", flush=True)
print(f"HTTP_SERVER_URL: {HTTP_SERVER_URL}", flush=True)
print(f"SEND_INTERVAL: {SEND_INTERVAL}", flush=True)
print(f"CSV_URL: {CSV_URL}", flush=True)
print(f"INSTANCE_DATA: {INSTANCE_DATA}", flush=True)

def download_csv(url):
    """Baixa o CSV da URL fornecida e o processa em uma lista de dicionários."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        return list(reader)
    except Exception as e:
        print(f"Erro ao baixar ou processar o CSV: {e}", flush=True)
        sys.exit(1)

def send_data_http(data, http_url):
    payload = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(http_url, data=payload, headers=headers)
        print(f"Dados enviados: {data}, Resposta do servidor: {response.status_code}, {response.text}", flush=True)
    except Exception as e:
        print(f"Erro ao enviar dados: {e}", flush=True)

def start_sending_data_http(data_list, http_url, unique_id, street):
    for data in data_list:
        data_to_send = {
            "type": "consumption",
            "id": unique_id,
            "street": street,
            **data
        }

        print("Enviando dados:", flush=True)
        print(data_to_send)

        send_data_http(data_to_send, http_url)
        time.sleep(SEND_INTERVAL)

if __name__ == '__main__':
    if not HTTP_SERVER_URL or not CSV_URL or not INSTANCE_DATA:
        print("Erro: As variáveis de ambiente 'CSV_URL', 'HTTP_SERVER_URL', e 'INSTANCE_DATA' devem ser definidas.", flush=True)
        sys.exit(1)

    # Carrega os dados da instância
    instance_data = json.loads(INSTANCE_DATA)
    unique_id = instance_data.get("id")
    street = instance_data.get("street")

    print("Dados da Instância Carregados:", flush=True)
    print(f"ID Único: {unique_id}")
    print(f"Endereço: {street}")

    # Baixa e processa o CSV
    print("Baixando e processando o CSV...", flush=True)
    data_list = download_csv(CSV_URL)

    print("Iniciando processo de envio", flush=True)
    start_sending_data_http(data_list, HTTP_SERVER_URL, unique_id, street)
    print("Medidor HTTP encerrado com sucesso.", flush=True)
