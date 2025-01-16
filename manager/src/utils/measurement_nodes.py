# utils/measurement_nodes.py

import os
import json
from dotenv import load_dotenv
from .config import load_json
from .nodes import create_node
from .general import normalize_container_name
from .docker_utils import list_containers

# Carregar variáveis do arquivo .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# Carregar caminhos dos arquivos JSON do .env
CONFIG_FILE = os.getenv("CONFIG_FILE")
BAIRROS_MEDIDORES_FILE = os.getenv("BAIRROS_MEDIDORES_FILE")
DOWNLOAD_URLS_FILE = os.getenv("DOWNLOAD_URLS_FILE")

if not CONFIG_FILE or not BAIRROS_MEDIDORES_FILE or not DOWNLOAD_URLS_FILE:
    raise ValueError("As variáveis CONFIG_FILE, BAIRROS_MEDIDORES_FILE e DOWNLOAD_URLS_FILE precisam ser definidas no .env.")

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

    # Buscar o contêiner correspondente no config.json
    container_data = next((c for c in config_data.get("containers", []) if c["name"] == container_name), None)
    if not container_data:
        print(f"Erro: Contêiner {container_name} não encontrado em {CONFIG_FILE}.")
        return

    # Obter o data_id do contêiner
    data_id = container_data.get("data_id")
    if not data_id:
        print(f"Erro: Nenhum 'data_id' configurado para o contêiner {container_name}.")
        return

    # Buscar a URL correspondente ao data_id
    download_url = data_urls.get(data_id)
    if not download_url:
        print(f"Erro: Nenhuma URL encontrada para 'data_id'={data_id} no contêiner {container_name}.")
        return

    # Obter todos os IDs existentes para evitar duplicatas
    existing_containers = list_containers(filters={"name": f"{normalize_container_name(bairro)}_{container_name}_"})
    existing_ids = {
        int(container.name.split("_")[-1])
        for container in existing_containers
        if container.name.startswith(f"{normalize_container_name(bairro)}_{container_name}_")
    }

    # Criar novos nós sequenciais
    for _ in range(quantity):
        # Encontrar o próximo ID disponível
        node_id = next(x for x in range(1, quantity + len(existing_ids) + 1) if x not in existing_ids)
        existing_ids.add(node_id)

        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{node_id}"

        print(f"[DEBUG] Criando nó {full_container_name} com URL de download {download_url}")

        # Configurar as variáveis de ambiente
        environment = {
            "HTTP_SERVER_URL": load_balancer_http_url,
            "COAP_SERVER_URL": load_balancer_coap_url,
            "CSV_URL": download_url,
            "INSTANCE_DATA": json.dumps({"node_id": str(node_id)}),
            "BAIRRO": bairro,
            "NODE_ID": str(node_id),
        }

        # Criar o nó usando a função `create_node`
        try:
            create_node(bairro, full_container_name, image, environment)
            print(f"[SUCESSO] Nó {full_container_name} criado com sucesso.")
        except Exception as e:
            print(f"Erro ao criar o nó {full_container_name}: {e}")
