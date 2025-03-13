import csv
import json
import requests
import time
import os
import sys

# Configuração das Variáveis de Ambiente
HTTP_SERVER_URL = os.getenv('HTTP_SERVER_URL')
SEND_INTERVAL = int(os.getenv('SEND_INTERVAL', 1))  # Intervalo de envio em segundos
CSV_URL = os.getenv('CSV_URL')
INSTANCE_DATA = os.getenv('INSTANCE_DATA')

print("Variáveis de Ambiente Recebidas:", flush=True)
print(f"HTTP_SERVER_URL: {HTTP_SERVER_URL}", flush=True)
print(f"SEND_INTERVAL: {SEND_INTERVAL}", flush=True)
print(f"CSV_URL: {CSV_URL}", flush=True)
print(f"INSTANCE_DATA: {INSTANCE_DATA}", flush=True)

def register_meter(http_url, unique_id, street, meter_type):
    """Registra o medidor no nó primário, informando o tipo (energia ou água)."""
    register_url = f"{http_url}/register_meter"
    payload = json.dumps({"id": unique_id, "street": street, "type": meter_type})
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(register_url, data=payload, headers=headers)
        if response.status_code == 200:
            print(f"Medidor {http_url} {unique_id} ({meter_type}) registrado com sucesso no nó primário.", flush=True)
            return True
        else:
            print(f"Erro ao registrar medidor {http_url} {unique_id} ({meter_type}): {response.status_code} - {response.text}", flush=True)
            return False
    except Exception as e:
        print(f"Erro ao registrar medidor {http_url} {unique_id}: {e}", flush=True)
        return False

def download_csv(url):
    """Baixa o CSV da URL fornecida e o processa em uma lista de dicionários."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()
        
        print("Primeiras 5 linhas do CSV baixado:", flush=True)
        for line in lines[:5]:
            print(line, flush=True)

        # Usar delimitador correto (';')
        reader = csv.DictReader(lines, delimiter=';')

        # Se não houver cabeçalhos, erro
        if reader.fieldnames is None:
            raise ValueError("O CSV não possui cabeçalhos.")

        # Verificar a presença dos campos de consumo
        available_nodes = {
            "consumption_m3_per_hour": [],  # Nodos de água
            "consumption_kwh_per_hour": []  # Nodos de energia
        }
        consumption_fields = [field for field in reader.fieldnames if field.startswith("consumption_")]

        print(f"Campos de consumo detectados: {', '.join(consumption_fields)}", flush=True)

        if "consumption_m3_per_hour" in consumption_fields:
            meter_type = "water"
        elif "consumption_kwh_per_hour" in consumption_fields:
            meter_type = "energy"
        else:
            meter_type = "desconhecido"

        print(f"Tipo de medidor detectado: {meter_type}", flush=True)

        data_list = []

        for row in reader:
            date = row.get("date", "").strip()
            time_ = row.get("time", "").strip()
            
            # Extrair campos de consumo
            consumption_data = {field: row.get(field, "").strip() for field in consumption_fields}
            
            # Se não houver dados, ignorar
            if not date or not time_ or not any(consumption_data.values()):
                print(f"Linha ignorada por falta de dados: {row}", flush=True)
                continue  
            
            data_to_add = {
                "date": date,
                "time": time_,
                **consumption_data
            }
            
            data_list.append(data_to_add)

        print(f"Total de linhas processadas: {len(data_list)}", flush=True)
        return data_list, meter_type

    except Exception as e:
        print(f"Erro ao baixar ou processar o CSV: {e}", flush=True)
        sys.exit(1)

def send_data_http(data, http_url):
    """Envia os dados via HTTP POST para o servidor especificado."""
    payload = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(http_url, data=payload, headers=headers)
        print(f"Dados enviados: {data}, Resposta: {response.status_code}, {response.text}", flush=True)
    except Exception as e:
        print(f"Erro ao enviar dados: {e}", flush=True)

def start_sending_data_http(data_list, http_url, unique_id, street, meter_type):
    """Inicia o envio dos dados em intervalos definidos."""
    try:
        while True:
            for data in data_list:
                data_to_send = {
                    "type": meter_type,
                    "id": unique_id,
                    "street": street,
                    **data
                }

                print("Enviando dados:", flush=True)
                print(data_to_send, flush=True)

                send_data_http(data_to_send, http_url)
                time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\nEnvio interrompido pelo usuário. Encerrando...", flush=True)
    except Exception as e:
        print(f"Erro inesperado no envio: {e}", flush=True)

if __name__ == '__main__':
    try:
        instance_data = json.loads(INSTANCE_DATA)
        unique_id = instance_data.get("id")
        street = instance_data.get("street")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar INSTANCE_DATA: {e}", flush=True)
        sys.exit(1)

    if unique_id is None or street is None:
        print("Erro: 'id' ou 'street' está faltando em INSTANCE_DATA.", flush=True)
        sys.exit(1)

    print("Dados da Instância Carregados:", flush=True)
    print(f"ID Único: {unique_id}", flush=True)
    print(f"Endereço: {street}", flush=True)

    # Baixar e processar o CSV para determinar o tipo do medidor
    print("Baixando e processando o CSV...", flush=True)
    data_list, meter_type = download_csv(CSV_URL)

    # Registrar o medidor com o tipo detectado
    print("Registrando medidor no nó primário...", flush=True)
    while not register_meter(HTTP_SERVER_URL, unique_id, street, meter_type):
        print("Tentando novamente em 5 segundos...", flush=True)
        time.sleep(5)

    print(f"Iniciando envio com intervalo de {SEND_INTERVAL} segundos...", flush=True)
    start_sending_data_http(data_list, HTTP_SERVER_URL, unique_id, street, meter_type)
