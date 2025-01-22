import csv
import json
import requests
import time
import sys

# Variáveis Fixas
HTTP_SERVER_URL = "http://127.0.0.1:8000/receive_data"  # URL local do servidor Flask
SEND_INTERVAL = 2  # Intervalo de envio em segundos
CSV_URL = "https://raw.githubusercontent.com/HenriqueBuzin/dissertation/main/data/data_energy.csv"
# CSV_URL = "https://raw.githubusercontent.com/HenriqueBuzin/dissertation/main/data/data_water.csv"
INSTANCE_DATA = '{"id": 1001, "street": "Rua da Praia, XXXX"}'

print("Variáveis Fixas Utilizadas:", flush=True)
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

        # Usar o delimitador correto
        reader = csv.DictReader(lines, delimiter=';')

        data_list = []

        # Verificar se os campos obrigatórios estão presentes
        required_fields = {'date', 'time'}
        missing_fields = required_fields - set(reader.fieldnames)
        if missing_fields:
            raise ValueError(f"Campos obrigatórios ausentes no CSV: {', '.join(missing_fields)}")

        # Identificar os campos de consumo (qualquer campo que comece com 'consumption_')
        consumption_fields = [field for field in reader.fieldnames if field.lower().startswith("consumption_")]
        if not consumption_fields:
            raise ValueError("Nenhum campo de consumo encontrado no CSV.")

        print(f"Campo(s) de consumo detectado(s): {', '.join(consumption_fields)}", flush=True)

        for row in reader:
            # Extrair os dados relevantes
            date = row.get("date", "").strip()
            time_ = row.get("time", "").strip()

            # Extrair os campos de consumo
            consumption_data = {field: row.get(field, "").strip() for field in consumption_fields}

            # Verificar se os campos obrigatórios estão presentes e se pelo menos um campo de consumo está preenchido
            if not date or not time_ or not any(consumption_data.values()):
                print(f"Linha com dados incompletos ignorada: {row}", flush=True)
                continue  # Pular linhas com dados incompletos

            # Construir o dicionário de dados a ser enviado
            data_to_add = {
                "date": date,
                "time": time_,
                **consumption_data  # Incluir todos os campos de consumo detectados
            }

            data_list.append(data_to_add)

        return data_list

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
        # Ignorar erros de envio conforme solicitado
        pass

def start_sending_data_http(data_list, http_url, unique_id, street):
    while True:  # Loop infinito
        for data in data_list:
            data_to_send = {
                "type": "consumption",
                "id": unique_id,
                "street": street,
                **data  # Incluir os dados de consumo específicos
            }

            print("Enviando dados:", flush=True)
            print(data_to_send, flush=True)

            send_data_http(data_to_send, http_url)
            time.sleep(SEND_INTERVAL)  # Espera o intervalo definido entre envios

if __name__ == '__main__':
    # Carrega os dados da instância
    instance_data = json.loads(INSTANCE_DATA)
    unique_id = instance_data.get("id")
    street = instance_data.get("street")

    print("Dados da Instância Carregados:", flush=True)
    print(f"ID Único: {unique_id}", flush=True)
    print(f"Endereço: {street}", flush=True)

    # Baixa e processa o CSV
    print("Baixando e processando o CSV...", flush=True)
    data_list = download_csv(CSV_URL)

    print("Iniciando processo de envio (Pressione Ctrl+C para encerrar)...", flush=True)
    try:
        start_sending_data_http(data_list, HTTP_SERVER_URL, unique_id, street)
    except KeyboardInterrupt:
        print("\nEnvio de dados interrompido pelo usuário. Encerrando...", flush=True)
    print("Medidor HTTP encerrado com sucesso.", flush=True)
