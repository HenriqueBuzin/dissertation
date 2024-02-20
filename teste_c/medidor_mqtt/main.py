import time
import csv
import paho.mqtt.client as mqtt

# Função para ler o CSV
def read_csv(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            yield row

# Callback chamado quando o cliente recebe uma resposta CONNACK do servidor.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

# Função para enviar dados usando MQTT
def send_data(data, topic, client):
    print(f"Tentando enviar dados: {data}")
    while True:
        try:
            info = client.publish(topic, str(data), qos=1)
            info.wait_for_publish()
            print(f"Dados enviados com sucesso: {data} \n")
            break  # Sai do loop após sucesso
        except Exception as e:
            print(f"Erro ao enviar dados: {e}. Tentando novamente...")
            client.reconnect()  # Tenta reconectar ao broker
            time.sleep(1)

# Função principal para iniciar o envio de dados
def start_sending_data(file_name, topic, client):
    for data in read_csv(file_name):
        data['type'] = 'consumption'
        # Supondo que 'id' seja único para cada execução
        data['id'] = 'unique_id_here'

        send_data(data, topic, client)
        time.sleep(1)

if __name__ == '__main__':
    # Configurações do MQTT
    mqtt_broker = 'broker.hivemq.com'
    mqtt_port = 1883
    mqtt_topic = 'your/topic/here'
    client = mqtt.Client()

    client.on_connect = on_connect  # Define o callback de conexão

    # Conectar ao broker
    client.connect(mqtt_broker, mqtt_port, 60)

    # Inicia um loop de rede em background para gerenciar a reconexão e a comunicação com o broker
    client.loop_start()

    file_name = 'data.csv'

    try:
        start_sending_data(file_name, mqtt_topic, client)
    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário. Encerrando o script.")
    finally:
        client.loop_stop()  # Para o loop de rede
        client.disconnect()  # Desconecta do broker
