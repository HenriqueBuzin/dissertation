# utils/netowrk.py

import socket
from .docker_utils import client
from .general import normalize_container_name

def create_or_get_bairro_network(bairro):
    """
    Cria (se não existir) e retorna o nome da rede Docker para o bairro especificado.
    """
    # Caso queira normalizar, faça:
    network_name = f"{normalize_container_name(bairro)}_network"

    existing_networks = client.networks.list(names=[network_name])
    if not existing_networks:
        client.networks.create(network_name, driver="bridge")
        print(f"Rede '{network_name}' criada.")
    else:
        print(f"Rede '{network_name}' já existe.")
    return network_name

def get_available_port(start_port=5000, end_port=6000):
    """Retorna uma porta disponível dentro do intervalo especificado."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def get_available_port(start_port=5000, end_port=6000):
    """Retorna uma porta disponível dentro do intervalo especificado."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def get_load_balancer_ports(containers):
    """Obtém as portas HTTP e CoAP do Load Balancer de um dos contêineres."""
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
