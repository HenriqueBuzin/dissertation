# utils/docker_utils.py

import docker

client = docker.from_env()

def list_containers(filters=None):

    """
    Lista os contêineres Docker existentes, com suporte a filtros.

    Args:
        filters (dict, optional): Dicionário de filtros para refinar a busca (exemplo: {"name": "example"}).

    Returns:
        list: Lista de contêineres correspondentes ao filtro fornecido.
    """

    return client.containers.list(all=True, filters=filters)

def get_container_logs(container_id, tail=50):

    """
    Obtém os últimos logs de um contêiner Docker.

    Args:
        container_id (str): ID ou nome do contêiner para obter os logs.
        tail (int, optional): Número de linhas finais dos logs a serem retornadas. Default é 50.

    Returns:
        str: Logs do contêiner em formato de string.
    """

    container = client.containers.get(container_id)
    return container.logs(tail=tail).decode("utf-8")

def get_available_port(containers):

    """
    Obtém as portas HTTP e CoAP disponíveis de um conjunto de contêineres.

    Args:
        containers (list): Lista de contêineres Docker a serem inspecionados.

    Returns:
        tuple: Par de portas (HTTP, CoAP), ou (None, None) se não encontradas.
    """

    for container in containers:
        ports = container.attrs["NetworkSettings"]["Ports"]
        http_port = ports.get("5000/tcp", [{}])[0].get("HostPort")
        coap_port = ports.get("5683/udp", [{}])[0].get("HostPort")
        if http_port and coap_port:
            return http_port, coap_port
    return None, None

def get_docker_client():

    """
    Retorna o cliente Docker configurado a partir do ambiente.

    Returns:
        docker.DockerClient: Instância do cliente Docker.
    """

    return docker.from_env()
