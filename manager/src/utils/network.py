# utils/netowrk.py

from .docker_utils import get_docker_client, get_docker_errors
from .general import normalize_container_name
from .docker_utils import get_docker_client
from contextlib import closing
import socket
import docker

def create_or_get_bairro_network(bairro):
    
    """
    Cria (se não existir) e retorna o nome da rede Docker para o bairro especificado.

    Args:
        bairro (str): Nome do bairro para o qual a rede será criada.

    Returns:
        str: Nome da rede Docker criada ou existente.
    """

    client = get_docker_client()

    network_name = f"{normalize_container_name(bairro)}_network"

    existing_networks = client.networks.list(names=[network_name])
    if not existing_networks:
        client.networks.create(network_name, driver="bridge")
        print(f"Rede '{network_name}' criada.")
    else:
        print(f"Rede '{network_name}' já existe.")
    return network_name

def create_or_get_lb_network():
    client = get_docker_client()
    _, _, _, NotFound = get_docker_errors()
    network_name = "load_balancers_network"

    try:
        client.networks.get(network_name)
        print(f"Rede '{network_name}' já existe.")
    except NotFound:
        ipam_pool = docker.types.IPAMPool(subnet="172.25.0.0/16")
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

        client.networks.create(
            name=network_name,
            driver="bridge",
            attachable=True,
            ipam=ipam_config
        )
        print(f"Rede '{network_name}' criada para Load Balancers.")

    return network_name

def get_available_port(start_port: int = 20000, end_port: int = 40000, host: str = "0.0.0.0", proto: str = "tcp") -> int:

    """
    Escolhe uma porta do *host* que:
      1) NÃO esteja publicada por nenhum container Docker (via inspeção do Docker), e
      2) passe no teste de bind local (para evitar conflito com processos fora do Docker).

    Observação: ainda existe pequena janela de corrida entre escolher e o Docker publicar.
    Para zerar a corrida, deixe o Docker escolher: passe ('127.0.0.1', None) no `ports`
    e depois leia a porta com `container.reload().attrs["NetworkSettings"]["Ports"]`.
    """

    # 1) portas que o Docker já está usando para este protocolo
    used_by_docker = _get_docker_published_host_ports(proto)

    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    socktype = socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM
    if proto not in ("tcp", "udp"):
        raise ValueError("proto deve ser 'tcp' ou 'udp'.")

    for port in range(start_port, end_port):
        if port in used_by_docker:
            continue
        # 2) teste de bind local (pega conflitos fora do Docker)
        with closing(socket.socket(family, socktype)) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue

    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def _get_docker_published_host_ports(proto: str | None = None) -> set[int]:

    """
    Varre TODOS os contêineres (running e stopped) e coleta as portas do host já publicadas.
    Se `proto` ("tcp"|"udp") for passado, filtra por protocolo.
    """
    
    used: set[int] = set()
    client = get_docker_client()
    # all=True: inclui parados que ainda reservam publicação (Docker conserva mapeamento até remover)
    for c in client.containers.list(all=True):
        try:
            ports = c.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
            for key, bindings in ports.items():  # key ex.: "5000/tcp"
                k_proto = key.split("/")[-1]
                if proto and k_proto != proto:
                    continue
                if not bindings:
                    continue
                for b in bindings:
                    hp = b.get("HostPort")
                    if hp:
                        used.add(int(hp))
        except Exception:
            # melhor ser tolerante aqui
            continue
    return used

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
