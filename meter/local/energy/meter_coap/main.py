import asyncio
import csv
import json
import multiprocessing
import signal
import sys
from aiocoap import *

CSV_FILE = 'data.csv'

def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row

async def send_data_coap(data, coap_url):
    context = await Context.create_client_context()
    payload = json.dumps(data).encode('utf-8')
    request = Message(code=POST, payload=payload, uri=coap_url)  # type: ignore

    print(f"Tentando enviar dados CoAP: {data}")
    try:
        response = await context.request(request).response
        print(f"Dados enviados com sucesso: {data}")
        print(f"Resposta do CoAP server: {response.code}, {response.payload.decode()}")
    except Exception as e:
        print(f"Falha ao enviar dados: {e}")

async def start_sending_data_coap(file_name, instance_id, stop_event, instance_info, coap_url):
    street = instance_info["street"]
    unique_id = instance_info["id"]
    
    stop_flag = False

    try:
        for data in read_csv(file_name):
            if stop_event.is_set():
                print(f"Processo {instance_id} encerrando...")
                break

            data['type'] = 'consumption'
            data['id'] = unique_id
            data['street'] = street

            try:
                await send_data_coap(data, coap_url)
                if stop_event.is_set():
                    break
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("Interrupção do teclado detectada. Finalizando o processo...")
                stop_flag = True
                break
    except asyncio.CancelledError:
        print(f"Processo {instance_id} cancelado.")
    finally:
        if stop_flag:
            print(f"Processo {instance_id} encerrado com sucesso.")

def signal_handler(signal, frame, processes, stop_event):
    print("\nCtrl+C detectado! Parando todos os processos...")
    stop_event.set()
    for process in processes:
        process.join()
    print("Medidor CoAP encerrado com sucesso.")
    sys.exit(0)

def run_process(instance_id, stop_event, bairro, docker_id, coap_url):
    with open(f'{bairro}.json') as f:
        instance_data = json.load(f)
    instance_info = instance_data["nodes"][str(docker_id)]
    try:
        asyncio.run(start_sending_data_coap(CSV_FILE, instance_id, stop_event, instance_info, coap_url))
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="CoAP Data Sender")
    parser.add_argument('instances', type=int, help='Number of instances to start')
    parser.add_argument('bairro', type=str, help='Bairro name to locate the data file')
    parser.add_argument('docker_id', type=int, help='Docker ID for the specific instance')
    parser.add_argument('coap_url', type=str, help='CoAP server URL for data sending')
    args = parser.parse_args()

    stop_event = multiprocessing.Event()
    processes = []

    try:
        for i in range(args.instances):
            instance_id = i + 1
            process = multiprocessing.Process(
                target=run_process,
                args=(instance_id, stop_event, args.bairro, args.docker_id, args.coap_url)
            )
            processes.append(process)
            process.start()

        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, processes, stop_event))

        for process in processes:
            process.join()
    except KeyboardInterrupt:
        pass
    finally:
        print("Medidor CoAP encerrado com sucesso.")
