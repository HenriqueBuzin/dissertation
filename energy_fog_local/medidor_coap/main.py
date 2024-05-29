import os
import asyncio
import csv
import json
from aiocoap import *

STREETS = [
    "1st Street", "2nd Street", "3rd Street", "4th Street", "5th Street",
    "6th Street", "7th Street", "8th Street", "9th Street", "10th Street",
    "11th Street", "12th Street", "13th Street", "14th Street", "15th Street",
    "16th Street", "17th Street", "18th Street", "19th Street", "20th Street"
]

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
    street = STREETS[(instance_id - 1) % len(STREETS)]
    for data in read_csv(file_name):
        data['type'] = 'consumption'
        data['id'] = instance_id
        data['street'] = street
        await send_data_coap(data, coap_url)
        await asyncio.sleep(1)

async def main():
    coap_url = os.getenv('URL')
    file_name = os.getenv('FILE')
    instance_id = int(os.getenv('INSTANCE_ID'))
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
