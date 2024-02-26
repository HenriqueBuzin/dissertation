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
    request = Message(code=POST, payload=payload, uri=coap_url)

    try:
        response = await context.request(request).response
        print(f"Dados enviados com sucesso: {data}")
        print(f"Resposta do CoAP server: {response.code}, {response.payload.decode()}")
    except Exception as e:
        print(f"Falha ao enviar dados: {e}")

async def start_sending_data_coap(file_name, coap_url):
    replica_id = "2"
    
    for data in read_csv(file_name):
        data['type'] = 'consumption'
        data['id'] = replica_id
        await send_data_coap(data, coap_url)
        await asyncio.sleep(1)

async def main():
    coap_url = 'coap://127.0.0.1:5683/coap'
    file_name = 'data.csv'
    await start_sending_data_coap(file_name, coap_url)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário. Encerrando o script.")
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
    finally:
        print("Finalizando recursos...")
        print("Script encerrado.")
