# utils/nodes.py

import docker
from .docker_utils import client
from .network import get_available_port
from .general import normalize_container_name

def create_node(bairro, container_name, image, container_types, load_balancer_url):
    """
    Cria um nó de névoa e o conecta ao Load Balancer do bairro.

    Args:
        bairro (str): Nome do bairro associado ao nó de névoa.
        container_name (str): Nome do contêiner a ser criado.
        image (str): Imagem Docker para o contêiner.
        container_types (dict): Tipos de contêineres disponíveis (para definir o ID do tipo).
        load_balancer_url (str): URL do Load Balancer para comunicação.

    Returns:
        tuple: (http_port, coap_port) se o nó for criado com sucesso, ou (None, None) em caso de erro.
    """
    try:
        # Obter portas disponíveis para HTTP e CoAP
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)

        # Normalizar o nome do contêiner
        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"

        # Verificar e remover contêineres antigos com o mesmo nome
        existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
        for container in existing_containers:
            print(f"Removendo contêiner antigo: {full_container_name}")
            container.stop()
            container.remove()

        # Criar o nó de névoa
        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            environment={
                "LOAD_BALANCER_URL": load_balancer_url,
                "FOG_NODE_NAME": full_container_name,
                "HTTP_PORT": str(http_port),
                "COAP_PORT": str(coap_port),
            },
            ports={
                "8000/tcp": http_port,  # Porta HTTP
                "5683/udp": coap_port,  # Porta CoAP
            },
            labels={"type": str(container_types["nodo_nevoa"]["id"])}  # Tipo específico para nós de névoa
        )
        print(f"Nó de névoa '{full_container_name}' criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}")
        return http_port, coap_port

    except docker.errors.APIError as e:
        print(f"Erro ao criar nó de névoa '{container_name}': {e}")
        return None, None
