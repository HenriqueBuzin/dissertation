# utils/nodes.py

import docker
from .docker_utils import client
from .general import normalize_container_name
from .network import get_available_port, create_or_get_bairro_network

def create_node(bairro, container_name, image, container_types, load_balancer_url):
    
    """
    Cria um nó de névoa e o conecta ao Load Balancer do bairro.

    Args:
        bairro (str): Nome do bairro onde o nó será criado.
        container_name (str): Nome base do contêiner.
        image (str): Imagem Docker para o nó.
        container_types (dict): Tipos de contêineres disponíveis no sistema.
        load_balancer_url (str): URL do Load Balancer ao qual o nó será conectado.

    Returns:
        tuple: Um par contendo a porta HTTP e a porta CoAP atribuídas ao nó, ou (None, None) em caso de erro.
    """

    try:
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)

        network_name = create_or_get_bairro_network(bairro)

        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"

        existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
        for container in existing_containers:
            print(f"Removendo contêiner antigo: {full_container_name}")
            container.stop()
            container.remove()

        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            network=network_name,
            environment={
                "LOAD_BALANCER_URL": load_balancer_url,
                "FOG_NODE_NAME": full_container_name,
                "HTTP_PORT": str(http_port),
                "COAP_PORT": str(coap_port),
            },
            ports={
                "8000/tcp": http_port,
                "5683/udp": coap_port,
            },
            labels={"type": str(container_types["nodo_nevoa"]["id"])}
        )
        print(f"Nó de névoa '{full_container_name}' criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}")
        return http_port, coap_port

    except docker.errors.APIError as e:
        print(f"Erro ao criar nó de névoa '{container_name}': {e}")
        return None, None