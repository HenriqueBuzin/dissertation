import os
import asyncio
import csv
import json
from aiocoap import *

def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row

async def send_data_coap(data, coap_url):
    context = await Context.create_client_context()
    payload = json.dumps(data).encode('utf-8')
    request = Message(code=POST, payload=payload, uri=coap_url) # type: ignore

    print(f"Tentando enviar dados CoAP: {data}")
    try:
        response = await context.request(request).response
        print(f"Dados enviados com sucesso: {data}")
        print(f"Resposta do CoAP server: {response.code}, {response.payload.decode()}")
    except Exception as e:
        print(f"Falha ao enviar dados: {e}")

async def start_sending_data_coap(file_name, coap_url, instance_id):
    for data in read_csv(file_name):
        data['type'] = 'consumption'
        data['id'] = instance_id
        await send_data_coap(data, coap_url)
        await asyncio.sleep(1)

async def main():
    coap_url = os.getenv('URL')
    file_name = os.getenv('FILE')
    instance_id = os.getenv('INSTANCE_ID')
    print(f"Iniciando a instância {instance_id}")
    await start_sending_data_coap(file_name, coap_url, instance_id)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMedidor CoAP encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução do Medidor CoAP: {e}")
    finally:
        print("Medidor CoAP encerrado com sucesso.")
