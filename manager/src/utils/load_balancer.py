# utils/load_balancer.py

import docker
from .docker_utils import client
from .network import get_available_port, create_or_get_bairro_network  # <-- Importar sua função de rede
from .general import normalize_container_name

def create_load_balancer(bairro, container_name, image, container_types):

    """
    Cria um Load Balancer com suporte a HTTP e CoAP para o bairro especificado.

    Args:
        bairro (str): Nome do bairro para o qual o Load Balancer será criado.
        container_name (str): Nome base do contêiner do Load Balancer.
        image (str): Imagem Docker a ser usada para o Load Balancer.
        container_types (dict): Dicionário contendo os tipos de contêineres e seus IDs.

    Returns:
        tuple: Um par contendo as portas HTTP e CoAP atribuídas ao Load Balancer ou (None, None) em caso de erro.

    Raises:
        docker.errors.APIError: Caso ocorra um erro ao interagir com a API do Docker.
    """
    
    try:
        # Obter portas disponíveis para HTTP e CoAP
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)

        # Criar/obter rede do bairro
        network_name = create_or_get_bairro_network(bairro)

        # Normalizar o nome do contêiner
        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"

        # Verificar e remover contêineres antigos com o mesmo nome
        existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
        for container in existing_containers:
            print(f"Removendo contêiner antigo: {full_container_name}")
            container.stop()
            container.remove()

        # Criar o Load Balancer
        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            network=network_name,  # <-- Adiciona o contêiner nesta rede
            environment={
                "LOAD_BALANCER_HTTP_PORT": str(http_port),
                "LOAD_BALANCER_COAP_PORT": str(coap_port),
            },
            ports={
                "5000/tcp": http_port,
                "5683/udp": coap_port,
            },
            labels={"type": str(container_types["load_balancer"]["id"])},
        )
        print(f"Load Balancer criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}")
        return http_port, coap_port

    except docker.errors.APIError as e:
        print(f"Erro ao criar Load Balancer: {e}")
        return None, None