# utils/netowrk.py

import socket
from .docker_utils import client
from .general import normalize_container_name

def create_or_get_bairro_network(bairro):
    
    """
    Cria (se não existir) e retorna o nome da rede Docker para o bairro especificado.

    Args:
        bairro (str): Nome do bairro para o qual a rede será criada.

    Returns:
        str: Nome da rede Docker criada ou existente.
    """

    network_name = f"{normalize_container_name(bairro)}_network"

    existing_networks = client.networks.list(names=[network_name])
    if not existing_networks:
        client.networks.create(network_name, driver="bridge")
        print(f"Rede '{network_name}' criada.")
    else:
        print(f"Rede '{network_name}' já existe.")
    return network_name

def get_available_port(start_port=5000, end_port=6000):
    
    """
    Retorna uma porta disponível dentro do intervalo especificado.

    Args:
        start_port (int): Porta inicial do intervalo (inclusiva).
        end_port (int): Porta final do intervalo (exclusiva).

    Returns:
        int: Uma porta disponível.

    Raises:
        RuntimeError: Se nenhuma porta estiver disponível no intervalo especificado.
    """
     
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def get_load_balancer_ports(containers):

    """
    Obtém as portas HTTP e CoAP associadas ao Load Balancer a partir de uma lista de contêineres Docker.

    A função percorre a lista de contêineres fornecida, inspecionando suas configurações de rede
    para localizar as portas mapeadas para HTTP (porta 5000) e CoAP (porta 5683). 
    Retorna o primeiro par de portas encontrado que corresponda a essas configurações.

    Args:
        containers (list): Lista de objetos de contêineres Docker obtidos pela API Docker.

    Returns:
        tuple: Um par de inteiros contendo as portas HTTP e CoAP mapeadas, no formato (http_port, coap_port).
               Caso não sejam encontradas, retorna (None, None).
    """
    
    for container in containers:
        try:
            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            http_port = ports.get("5000/tcp", [{}])[0].get("HostPort")
            coap_port = ports.get("5683/udp", [{}])[0].get("HostPort")
            if http_port and coap_port:
                return http_port, coap_port
        except (KeyError, TypeError, IndexError):
            continue
    return None, None
