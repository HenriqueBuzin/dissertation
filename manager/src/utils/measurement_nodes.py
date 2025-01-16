# utils/measurement_nodes.py

import os
import json
from .docker_utils import client
from .network import create_network
from .config import load_json
from .nodes import create_node
from .general import normalize_container_name

# Definir os caminhos para os arquivos JSON usando o diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório do arquivo atual
PROJECT_DIR = os.path.dirname(BASE_DIR)  # Diretório do projeto
JSON_PATH = os.path.join(PROJECT_DIR, "jsons")

CONFIG_FILE = os.path.join(JSON_PATH, "config.json")
BAIRROS_MEDIDORES_FILE = os.path.join(JSON_PATH, "bairros_medidores.json")
DOWNLOAD_URLS_FILE = os.path.join(JSON_PATH, "download_urls.json")


def create_measurement_nodes(
    bairro, container_name, image, quantity, load_balancer_http_port, load_balancer_coap_port, container_types
):
    """
    Cria múltiplos nós de medição e os conecta ao Load Balancer.

    Args:
        bairro (str): Nome do bairro.
        container_name (str): Nome base do contêiner.
        image (str): Imagem Docker para os nós.
        quantity (int): Quantidade de nós a serem criados.
        load_balancer_http_port (int): Porta HTTP do Load Balancer.
        load_balancer_coap_port (int): Porta CoAP do Load Balancer.
        container_types (dict): Tipos de contêineres disponíveis.
    """
    # Carregar os dados de configuração e URLs
    config_data = load_json(CONFIG_FILE, default={})
    data_urls = load_json(DOWNLOAD_URLS_FILE, default={})

    # URLs do Load Balancer
    load_balancer_http_url = f"http://host.docker.internal:{load_balancer_http_port}/receive_data"
    load_balancer_coap_url = f"coap://host.docker.internal:{load_balancer_coap_port}/receive_data"

    print(f"[DEBUG] URLs do Load Balancer: HTTP: {load_balancer_http_url}, CoAP: {load_balancer_coap_url}")

    for i in range(1, quantity + 1):
        node_id = str(i)
        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{node_id}"  # Inclui o nome do bairro

        # Buscar o contêiner correspondente no config.json
        container_data = next((c for c in config_data.get("containers", []) if c["name"] == container_name), None)
        if not container_data:
            print(f"Erro: Contêiner {container_name} não encontrado em {CONFIG_FILE}.")
            continue

        # Obter o data_id do contêiner
        data_id = container_data.get("data_id")
        if not data_id:
            print(f"Erro: Nenhum 'data_id' configurado para o contêiner {container_name}.")
            continue

        # Buscar a URL correspondente ao data_id
        download_url = data_urls.get(data_id)
        if not download_url:
            print(f"Erro: Nenhuma URL encontrada para 'data_id'={data_id} no contêiner {container_name}.")
            continue

        print(f"[DEBUG] Criando nó {full_container_name} com URL de download {download_url}")

        # Configurar as variáveis de ambiente
        environment = {
            "HTTP_SERVER_URL": load_balancer_http_url,
            "COAP_SERVER_URL": load_balancer_coap_url,
            "CSV_URL": download_url,
            "INSTANCE_DATA": json.dumps({"node_id": node_id}),
            "BAIRRO": bairro,
            "NODE_ID": node_id,
        }

        # Criar o nó usando a função `create_node`
        try:
            create_node(bairro, full_container_name, image, environment)
            print(f"[SUCESSO] Nó {full_container_name} criado com sucesso.")
        except Exception as e:
            print(f"Erro ao criar o nó {full_container_name}: {e}")
