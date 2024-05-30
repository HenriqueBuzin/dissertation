import csv
import json
import multiprocessing
import signal
import sys
import requests
import time

CSV_FILE = 'data.csv'
HTTP_SERVER_URL = 'http://localhost:8000'  # URL do servidor HTTP

class DevNull:
    def write(self, msg):
        pass

def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row

def send_data_http(data, http_url):
    payload = json.dumps(data)
    headers = {'Content-Type': 'application/json'}

    print(f"Tentando enviar dados HTTP: {data}")
    try:
        response = requests.post(http_url, data=payload, headers=headers)
        print(f"Dados enviados com sucesso: {data}")
        print(f"Resposta do servidor HTTP: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Falha ao enviar dados: {e}")

def start_sending_data_http(file_name, http_url, instance_id, stop_event):
    street = f"{instance_id}st Street"
    stop_flag = False

    for data in read_csv(file_name):
        if stop_event.is_set():
            print(f"Processo {instance_id} encerrando...")
            break

        data['type'] = 'consumption'
        data['id'] = instance_id
        data['street'] = street

        try:
            send_data_http(data, http_url)
            time.sleep(1)
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
    print("Medidor HTTP encerrado com sucesso.")
    sys.exit(0)

def run_process(instance_id, stop_event):
    start_sending_data_http(CSV_FILE, HTTP_SERVER_URL, instance_id, stop_event)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="HTTP Data Sender")
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
        print("Medidor HTTP encerrado com sucesso.")
