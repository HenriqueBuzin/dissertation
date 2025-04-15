# utils/load_balancer.py

from .network import get_available_port, create_or_get_bairro_network, create_or_get_lb_network
from .docker_utils import get_docker_client, get_docker_errors
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
    client = get_docker_client()
    APIError = get_docker_errors()[2]

    try:
        
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)

        bairro_network = create_or_get_bairro_network(bairro)
        lb_network = create_or_get_lb_network()

        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"

        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            network=lb_network,
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

        client.networks.get(bairro_network).connect(full_container_name)

        print(f"Load Balancer criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}")
        return http_port, coap_port

    except APIError as e:
        print(f"[ERRO] Falha ao criar o Load Balancer '{full_container_name}': {e}")
        return None, None
