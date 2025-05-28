import os
import json
import time
import csv
import requests
import sys
import paho.mqtt.client as mqtt

# Variáveis de ambiente
CSV_URL = os.getenv('CSV_URL')
INSTANCE_DATA = os.getenv('INSTANCE_DATA')
MQTT_BROKER_URL = os.getenv('MQTT_BROKER_URL')
MQTT_TOPIC_DATA = os.getenv('MQTT_TOPIC_DATA')
SEND_INTERVAL = int(os.getenv('SEND_INTERVAL', 1))
MQTT_TOPIC_REGISTER = os.getenv('MQTT_TOPIC_REGISTER')

print("Variáveis de Ambiente Recebidas:", flush=True)
print(f"CSV_URL: {CSV_URL}", flush=True)
print(f"INSTANCE_DATA: {INSTANCE_DATA}", flush=True)
print(f"MQTT_BROKER_URL: {MQTT_BROKER_URL}", flush=True)
print(f"MQTT_TOPIC_DATA: {MQTT_TOPIC_DATA}", flush=True)
print(f"SEND_INTERVAL: {SEND_INTERVAL}", flush=True)
print(f"MQTT_TOPIC_REGISTER: {MQTT_TOPIC_REGISTER}", flush=True)

# MQTT Client
mqtt_client = mqtt.Client()

# Conectar ao broker
mqtt_client.connect(MQTT_BROKER_URL)
mqtt_client.loop_start()

# Parse instance data
try:
    instance = json.loads(INSTANCE_DATA)
    unique_id = instance.get("id")
    street = instance.get("street")
except json.JSONDecodeError:
    print("Erro ao interpretar INSTANCE_DATA.", flush=True)
    sys.exit(1)

def download_csv(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()
        reader = csv.DictReader(lines, delimiter=';')

        if reader.fieldnames is None:
            raise ValueError("O CSV não possui cabeçalhos.")

        consumption_fields = [field for field in reader.fieldnames if field.startswith("consumption_")]

        if "consumption_m3_per_hour" in consumption_fields:
            meter_type = "water"
        elif "consumption_kwh_per_hour" in consumption_fields:
            meter_type = "energy"
        else:
            meter_type = "desconhecido"

        data_list = []
        for row in reader:
            date = row.get("date", "").strip()
            time_ = row.get("time", "").strip()
            consumption = {k: row.get(k, "").strip() for k in consumption_fields}

            if not date or not time_ or not any(consumption.values()):
                continue

            data_list.append({
                "date": date,
                "time": time_,
                **consumption
            })

        return data_list, meter_type

    except Exception as e:
        print(f"Erro ao processar CSV: {e}", flush=True)
        sys.exit(1)

def register_meter(meter_type):
    payload = {
        "id": unique_id,
        "street": street,
        "type": meter_type
    }
    mqtt_client.publish(MQTT_TOPIC_REGISTER, json.dumps(payload))
    print(f"[MQTT] Medidor registrado no tópico {MQTT_TOPIC_REGISTER}: {payload}", flush=True)

def send_data_loop(data_list, meter_type):
    try:
        for data in data_list:
            message = {
                "type": meter_type,
                "id": unique_id,
                "street": street,
                **data
            }

            mqtt_client.publish(MQTT_TOPIC_DATA, json.dumps(message))
            print(f"[MQTT] Dados enviados para {MQTT_TOPIC_DATA}: {message}", flush=True)
            time.sleep(SEND_INTERVAL)

        print("Todos os dados foram enviados com sucesso.", flush=True)
    except KeyboardInterrupt:
        print("Envio interrompido.", flush=True)
    except Exception as e:
        print(f"Erro ao enviar dados: {e}", flush=True)

# Execução principal
if __name__ == "__main__":
    print("Baixando e processando o CSV...", flush=True)
    data_list, meter_type = download_csv(CSV_URL)

    print("Registrando medidor via MQTT...", flush=True)
    register_meter(meter_type)

    print("Iniciando envio dos dados via MQTT...", flush=True)
    send_data_loop(data_list, meter_type)
