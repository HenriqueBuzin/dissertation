import asyncio
import csv
import json
import os
import sys
from aiocoap import *

COAP_SERVER_URL = os.getenv('COAP_SERVER_URL')
SEND_INTERVAL = int(os.getenv('SEND_INTERVAL', 1))
CSV_URL = os.getenv('CSV_URL')
INSTANCE_DATA = os.getenv('INSTANCE_DATA')

print("Variáveis de Ambiente Recebidas:")
print(f"COAP_SERVER_URL: {COAP_SERVER_URL}")
print(f"SEND_INTERVAL: {SEND_INTERVAL}")
print(f"CSV_URL: {CSV_URL}")
print(f"INSTANCE_DATA: {INSTANCE_DATA}")

def download_csv(url):
    """Baixa o CSV da URL fornecida e o processa em uma lista de dicionários."""
    try:
        import requests
        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        return list(reader)
    except Exception as e:
        print(f"Erro ao baixar ou processar o CSV: {e}")
        sys.exit(1)

async def send_data_coap(data, coap_url):
    """Envia os dados para o servidor CoAP."""
    context = await Context.create_client_context()
    payload = json.dumps(data).encode('utf-8')
    request = Message(code=POST, payload=payload, uri=coap_url)

    try:
        print(f"Tentando enviar dados CoAP: {data}")
        response = await context.request(request).response
        print(f"Dados enviados com sucesso! Resposta: {response.code}, {response.payload.decode()}")
    except Exception as e:
        print(f"Falha ao enviar dados CoAP: {e}")

async def start_sending_data_coap(data_list, coap_url, unique_id, street):
    """Envia os dados do CSV periodicamente via CoAP."""
    for data in data_list:
        data_to_send = {
            "type": "consumption",
            "id": unique_id,
            "street": street,
            **data
        }

        print("Enviando dados via CoAP:")
        print(data_to_send)

        await send_data_coap(data_to_send, coap_url)
        await asyncio.sleep(SEND_INTERVAL)

if __name__ == '__main__':
    if not COAP_SERVER_URL or not CSV_URL or not INSTANCE_DATA:
        print("Erro: As variáveis de ambiente 'CSV_URL', 'COAP_SERVER_URL', e 'INSTANCE_DATA' devem ser definidas.")
        sys.exit(1)

    # Carrega os dados da instância
    instance_data = json.loads(INSTANCE_DATA)
    unique_id = instance_data.get("id")
    street = instance_data.get("street")

    print("Dados da Instância Carregados:")
    print(f"ID Único: {unique_id}")
    print(f"Endereço: {street}")

    # Baixa e processa o CSV
    print("Baixando e processando o CSV...")
    data_list = download_csv(CSV_URL)

    print("Iniciando processo de envio CoAP...")
    asyncio.run(start_sending_data_coap(data_list, COAP_SERVER_URL, unique_id, street))
    print("Medidor CoAP encerrado com sucesso.")
