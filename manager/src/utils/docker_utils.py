# utils/docker_utils.py

import docker

client = docker.from_env()

def list_containers(filters=None):
    return client.containers.list(all=True, filters=filters)

def get_container_logs(container_id, tail=50):
    container = client.containers.get(container_id)
    return container.logs(tail=tail).decode("utf-8")

def get_available_port(containers):
    for container in containers:
        ports = container.attrs["NetworkSettings"]["Ports"]
        http_port = ports.get("5000/tcp", [{}])[0].get("HostPort")
        coap_port = ports.get("5683/udp", [{}])[0].get("HostPort")
        if http_port and coap_port:
            return http_port, coap_port
    return None, None

def get_docker_client():
    """Retorna o cliente Docker configurado."""
    return docker.from_env()
