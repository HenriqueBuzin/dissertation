import requests
import time
import csv
import argparse

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

def start_sending_data(file_name, url, instance_id):
    street = STREETS[(instance_id - 1) % len(STREETS)]
    for index, data in enumerate(read_csv(file_name), start=1):
        data['type'] = 'consumption'
        data['id'] = instance_id
        data['street'] = street
        send_data(data, url)
        time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HTTP Data Sender")
    parser.add_argument('--file', type=str, required=True, help='CSV file name')
    parser.add_argument('--url', type=str, required=True, help='Server URL')
    parser.add_argument('--instance_id', type=int, required=True, help='Instance ID')
    args = parser.parse_args()

    try:
        start_sending_data(args.file, args.url, args.instance_id)
    except KeyboardInterrupt:
        print("\nMedidor HTTP encerrando...")
    except Exception as e:
        print(f"\nErro durante a execução do Medidor HTTP: {e}")
    finally:
        print("Medidor HTTP encerrado com sucesso.")
