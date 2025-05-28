import os
import json
import logging
from paho.mqtt.client import Client
import asyncio
from http_server import distribute_data

logging.basicConfig(level=logging.INFO)

MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC  = os.getenv("MQTT_TOPIC_DATA", "sensors/data")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"[MQTT] Conectado ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logging.info(f"[MQTT] Inscrito no tópico: {MQTT_TOPIC}")
    else:
        logging.error(f"[MQTT] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        logging.info(f"[MQTT ← RECEIVE] {data}")
        asyncio.run(distribute_data(data))
    except Exception as e:
        logging.error(f"[MQTT] Erro ao processar mensagem: {e}")

async def start_mqtt_server(port=None):
    client = Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, port or MQTT_PORT, 60)
    client.loop_start()  # <-- roda em background (não bloqueante)

    logging.info(f"[MQTT] Cliente iniciado e rodando em segundo plano")
    while True:
        await asyncio.sleep(3600)  # mantém a função viva
