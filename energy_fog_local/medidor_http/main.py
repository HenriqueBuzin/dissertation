import os
import asyncio
import csv
import json
import multiprocessing
import signal
import sys
from aiocoap import *

CSV_FILE = 'data.csv'
COAP_SERVER_URL = 'coap://localhost:5683'

STREETS = [
    "1st Street", "2nd Street", "3rd Street", "4th Street", "5th Street",
    "6th Street", "7th Street", "8th Street", "9th Street", "10th Street",
    "11th Street", "12th Street", "13th Street", "14th Street", "15th Street",
    "16th Street", "17th Street", "18th Street", "19th Street", "20th Street"
]

class DevNull:
    def write(self, msg):
        pass

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

async def start_sending_data_coap(file_name, coap_url, instance_id, stop_event):
    street = STREETS[(instance_id - 1) % len(STREETS)]
    stop_flag = False

    for data in read_csv(file_name):
        if stop_event.is_set():
            print(f"Processo {instance_id} encerrando...")
            break

        data['type'] = 'consumption'
        data['id'] = instance_id
        data['street'] = street

        try:
            await send_data_coap(data, coap_url)
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Interrupção do teclado detectada. Finalizando o processo...")
            stop_flag = True
            break

    if stop_flag:
        print(f"Processo {instance_id} encerrado com sucesso.")

def signal_handler(signal, frame, processes, stop_event):
    print("\nCtrl+C detected! Stopping all processes...")
    stop_event.set()
    for process in processes:
        process.join()
    print("Medidor CoAP encerrado com sucesso.")
    sys.exit(0)

def run_process(instance_id, stop_event):
    asyncio.run(start_sending_data_coap(CSV_FILE, COAP_SERVER_URL, instance_id, stop_event))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="CoAP Data Sender")
    parser.add_argument('instances', type=int, help='Number of instances to start')
    args = parser.parse_args()

    stop_event = multiprocessing.Event()
    processes = []

    try:
        for i in range(args.instances):
            instance_id = i + 1
            process = multiprocessing.Process(target=run_process, args=(instance_id, stop_event))
            processes.append(process)
            process.start()

        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, processes, stop_event))

        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\nCtrl+C detected! Stopping all processes...")
        stop_event.set()
        for process in processes:
            process.join()
    finally:
        print("Medidor CoAP encerrado com sucesso.")
