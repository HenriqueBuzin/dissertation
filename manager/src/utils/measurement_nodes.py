# utils/measurement_nodes.py

import os
import json
from dotenv import load_dotenv
from .config import load_json
from .general import normalize_container_name
from .docker_utils import client, list_containers
from .network import get_available_port, create_or_get_bairro_network

# Carregar variáveis do arquivo .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# Carregar caminhos dos arquivos JSON do .env
CONFIG_FILE = os.getenv("CONFIG_FILE")
BAIRROS_MEDIDORES_FILE = os.getenv("BAIRROS_MEDIDORES_FILE")
DOWNLOAD_URLS_FILE = os.getenv("DOWNLOAD_URLS_FILE")

# Verificar se todas as variáveis necessárias estão definidas
if not CONFIG_FILE or not BAIRROS_MEDIDORES_FILE or not DOWNLOAD_URLS_FILE:
    raise ValueError("As variáveis CONFIG_FILE, BAIRROS_MEDIDORES_FILE e DOWNLOAD_URLS_FILE precisam estar definidas no .env.")

def create_measurement_node(bairro, full_container_name, image, environment, labels):
    
    """
    Cria um nó de medição (medidor) em uma rede Docker associada a um bairro.

    Esta função cria e inicia um contêiner Docker representando um medidor de dados. Ele é conectado
    à rede Docker do bairro, configurado com as variáveis de ambiente fornecidas e mapeado para
    portas disponíveis para comunicação via HTTP e CoAP.

    Args:
        bairro (str): Nome do bairro associado ao nó.
        full_container_name (str): Nome completo do contêiner no formato "<bairro>_<nome>_<id>".
        image (str): Imagem Docker a ser utilizada para o contêiner.
        environment (dict): Variáveis de ambiente a serem configuradas no contêiner.
        labels (dict): Labels para identificação do contêiner.

    Returns:
        tuple: Par de portas (http_port, coap_port) atribuídas ao contêiner. Retorna (None, None) em caso de erro.

    Raises:
        docker.errors.APIError: Caso ocorra um erro durante a criação ou execução do contêiner.
    """

    try:
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)

        # Criar/obter a rede do bairro
        network_name = create_or_get_bairro_network(bairro)

        # Verificar e remover contêineres antigos com o mesmo nome
        existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
        for container in existing_containers:
            print(f"Removendo contêiner antigo: {full_container_name}")
            container.stop()
            container.remove()

        # Criar o contêiner
        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            network=network_name,
            environment=environment,  # environment vem de quem chamou
            ports={
                "8000/tcp": http_port,
                "5683/udp": coap_port,
            },
            labels=labels             # labels vem de quem chamou
        )
        print(f"[SUCESSO] Medidor '{full_container_name}' criado. HTTP: {http_port}, CoAP: {coap_port}")
        return http_port, coap_port

    except docker.errors.APIError as e:
        print(f"[ERRO] Falha ao criar o medidor {full_container_name}: {e}")
        return None, None

def create_measurement_nodes(
    bairro, container_name, image, quantity, load_balancer_http_port, load_balancer_coap_port
):
    
    """
    Cria múltiplos nós de medição e os conecta ao Load Balancer do bairro.

    Esta função gerencia a criação de vários contêineres Docker que atuam como medidores. Cada medidor
    é configurado para enviar dados a um Load Balancer via HTTP e CoAP, utilizando URLs e informações
    especificadas nos arquivos de configuração.

    Args:
        bairro (str): Nome do bairro associado aos nós de medição.
        container_name (str): Nome base dos contêineres a serem criados.
        image (str): Imagem Docker utilizada para os nós de medição.
        quantity (int): Número de nós de medição a serem criados.
        load_balancer_http_port (int): Porta HTTP do Load Balancer para envio de dados.
        load_balancer_coap_port (int): Porta CoAP do Load Balancer para envio de dados.

    Raises:
        ValueError: Caso alguma configuração ou URL necessária não seja encontrada.

    Behavior:
        1. Carrega os dados do arquivo de configuração (`config.json`) e as URLs de download.
        2. Verifica contêineres existentes para evitar duplicação de IDs.
        3. Gera nomes exclusivos para cada novo nó e monta as configurações necessárias.
        4. Cria os nós de medição chamando a função `create_measurement_node`.
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
        raise ValueError(f"Erro: Contêiner {container_name} não encontrado em {CONFIG_FILE}.")

    # Obter o data_id do contêiner
    data_id = container_data.get("data_id")
    if not data_id:
        raise ValueError(f"Erro: Nenhum 'data_id' configurado para o contêiner {container_name}.")

    # Buscar a URL correspondente ao data_id
    download_url = data_urls.get(data_id)
    if not download_url:
        raise ValueError(f"Erro: Nenhuma URL encontrada para 'data_id'={data_id} no contêiner {container_name}.")

    # Verificar contêineres existentes
    existing_containers = list_containers(filters={"name": f"{normalize_container_name(bairro)}_{container_name}_"})
    existing_ids = {
        int(container.name.split("_")[-1])
        for container in existing_containers
        if container.name.startswith(f"{normalize_container_name(bairro)}_{container_name}_")
    }

    # Determinar o tipo para os labels
    container_type = container_data.get("type", "unknown")

    # Criar múltiplos nós
    for _ in range(quantity):
        # Encontrar o próximo ID disponível
        node_id = next(x for x in range(1, quantity + len(existing_ids) + 1) if x not in existing_ids)
        existing_ids.add(node_id)

        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{node_id}"
        print(f"[DEBUG] Criando nó {full_container_name} com URL de download {download_url}")

        # Montar environment
        environment = {
            "HTTP_SERVER_URL": load_balancer_http_url,
            "COAP_SERVER_URL": load_balancer_coap_url,
            "CSV_URL": download_url,
            "INSTANCE_DATA": json.dumps({"node_id": str(node_id)}),
            "BAIRRO": bairro,
            "NODE_ID": str(node_id),
        }

        # Montar labels
        labels = {
            "type": str(container_type)
        }

        # Criar cada medidor chamando create_measurement_node
        create_measurement_node(
            bairro, full_container_name, image, environment, labels
        )
