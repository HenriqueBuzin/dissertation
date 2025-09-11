# utils/nodes.py

from ..network import get_available_port, create_or_get_bairro_network
from ..docker_utils import get_docker_client, list_containers, get_docker_errors
from ..general import normalize_container_name
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

def create_node(bairro, container_name, image, container_types, load_balancer_url, quantity):
    
    """
    Cria múltiplos nós de névoa e os conecta ao Load Balancer e ao Agregador do bairro.

    Args:
        bairro (str): Nome do bairro onde os nós serão criados.
        container_name (str): Nome base dos contêineres que serão criados.
        image (str): Imagem Docker utilizada para criar os nós de névoa.
        container_types (dict): Dicionário contendo os tipos de contêineres e seus IDs.
        load_balancer_url (str): URL do Load Balancer ao qual os nós de névoa se conectarão.
        quantity (int): Número de nós de névoa que serão criados.

    Returns:
        list: Lista de tuplas contendo as portas HTTP e CoAP atribuídas a cada nó criado.

    Raises:
        docker.errors.APIError: Caso ocorra um erro ao interagir com a API do Docker.
        docker.errors.ContainerError: Caso o contêiner não seja iniciado corretamente.
        docker.errors.ImageNotFound: Caso a imagem Docker especificada não seja encontrada.
        ValueError: Caso o agregador do bairro não seja encontrado.
        Exception: Para qualquer outro erro inesperado.
    """

    client = get_docker_client()
    ContainerError, ImageNotFound, APIError, _ = get_docker_errors()

    created_nodes = []

    try:
        network_name = create_or_get_bairro_network(bairro)

        aggregator_name = f"{normalize_container_name(bairro)}_aggregator"
        aggregator_container = next(
            (c for c in list_containers(filters={"name": aggregator_name})), None
        )
        if not aggregator_container:
            raise ValueError(f"Agregador para o bairro '{bairro}' não encontrado.")
        
        existing_containers = list_containers(filters={"name": f"{normalize_container_name(bairro)}_{container_name}"})
        count = len(existing_containers) + 1

        for _ in range(quantity):
            http_port = get_available_port()
            coap_port = get_available_port(http_port + 1)

            full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{count}"

            print(f"[INFO] Criando nó de névoa '{full_container_name}' com HTTP_PORT={http_port}, COAP_PORT={coap_port}...")

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
                    "AGGREGATOR_HOST": aggregator_name,
                    "AGGREGATOR_PORT": os.environ["AGGREGATOR_PORT"],
                    "AGGREGATOR_USER": os.environ["AGGREGATOR_USER"],
                    "AGGREGATOR_PASS": os.environ["AGGREGATOR_PASS"],
                    "AGGREGATOR_INCOMING_DIR": os.environ["AGGREGATOR_INCOMING_DIR"],
                    "NODE_SEND_INTERVAL": os.environ["NODE_SEND_INTERVAL"],
                },
                ports={
                    "8000/tcp": http_port,
                    "5683/udp": coap_port,
                },
                labels={
                    "type": str(container_types["nodo_nevoa"]["id"])
                }
            )
            print(f"[SUCESSO] Nó de névoa '{full_container_name}' criado com sucesso. HTTP: {http_port}, COAP: {coap_port}")
            created_nodes.append((http_port, coap_port))
            count += 1

    except ContainerError as e:
        print(f"[ERRO] O contêiner '{container_name}' encontrou um erro ao ser executado: {e}")
    except ImageNotFound:
        print(f"[ERRO] Imagem '{image}' não encontrada.")
    except APIError as e:
        print(f"[ERRO] Erro na API Docker: {e}")
    except ValueError as ve:
        print(f"[ERRO] {ve}")
    except Exception as e:
        print(f"[ERRO] Erro desconhecido ao criar nó(s) de névoa: {e}")

    return created_nodes
