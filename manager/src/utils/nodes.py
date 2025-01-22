# utils/nodes.py

import docker
from .docker_utils import client, list_containers
from .general import normalize_container_name
from .network import get_available_port, create_or_get_bairro_network

def create_node(bairro, container_name, image, container_types, load_balancer_url, quantity):

    """
    Cria múltiplos nós de névoa e os conecta ao Load Balancer do bairro.

    Args:
        bairro (str): Nome do bairro onde os nós serão criados.
        container_name (str): Nome base dos contêineres.
        image (str): Imagem Docker para os nós.
        container_types (dict): Tipos de contêineres disponíveis no sistema.
        load_balancer_url (str): URL do Load Balancer ao qual os nós serão conectados.
        quantity (int): Número de nós a serem criados.

    Returns:
        list: Lista de pares (http_port, coap_port) para os nós criados.
    """

    created_nodes = []

    try:
        network_name = create_or_get_bairro_network(bairro)
        existing_containers = list_containers(filters={"name": f"{normalize_container_name(bairro)}_{container_name}"})

        count = len(existing_containers) + 1  # Define o ponto inicial para os novos contêineres

        for _ in range(quantity):
            http_port = get_available_port()
            coap_port = get_available_port(http_port + 1)

            full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{count}"

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
                labels={
                    "type": str(container_types["nodo_nevoa"]["id"])
                }
            )
            print(f"Nó de névoa '{full_container_name}' criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}")
            created_nodes.append((http_port, coap_port))
            count += 1  # Incrementa o contador para o próximo nó

    except docker.errors.APIError as e:
        print(f"Erro na API Docker: {e}")
    except docker.errors.ImageNotFound:
        print(f"Erro: Imagem '{image}' não encontrada.")
    except Exception as e:
        print(f"Erro desconhecido ao criar nó(s) de névoa: {e}")

    return created_nodes