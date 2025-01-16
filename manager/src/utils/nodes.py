# utils/nodes.py

from .docker_utils import client

def create_node(bairro, node_name, image, environment):
    network_name = f"{bairro}_network"
    client.containers.run(
        image, name=node_name, network=network_name, detach=True, environment=environment
    )
    print(f"Nó {node_name} criado na rede {bairro}.")
