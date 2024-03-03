import requests
import time
import csv

def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row

def send_data(data, url):
    while True:
        print(f"Tentando enviar dados: {data}")
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Dados enviados com sucesso: {data} \n")
                break
            else:
                print(f"Erro ao enviar dados (status code {response.status_code}). Tentando novamente... \n")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar dados: {e}. Tentando novamente...")
        time.sleep(1)

def start_sending_data(file_name, url):
    replica_id = "1"

    for data in read_csv(file_name):
        data['type'] = 'consumption'
        data['id'] = replica_id

        send_data(data, url)
        time.sleep(1)

if __name__ == '__main__':
    url = 'http://127.0.0.1:8000'
    file_name = 'data.csv'

    try:
        start_sending_data(file_name, url)
    except KeyboardInterrupt:
        print("\nMedidor HTTP encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução do Medidor HTTP: {e}")
    finally:
        print("Medidor HTTP encerrado com sucesso.")
