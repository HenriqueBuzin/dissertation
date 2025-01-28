# utils/aggregator.py

from utils.docker_utils import client

def create_aggregator(bairro, image, container_types):
    """Cria o agregador para um bairro."""
    network_name = f"{bairro}_network"
    container_name = f"{bairro}_aggregator"

    try:
        print(f"[INFO] Tentando criar o agregador '{container_name}' na rede '{network_name}'...")

        # Criação do contêiner Docker
        client.containers.run(
            image,
            name=container_name,
            network=network_name,
            detach=True,
            ports={"8000/tcp": None},
            environment={"BAIRRO": bairro},
            labels={"type": str(container_types["aggregator"]["id"])}
        )
        
        print(f"[SUCESSO] Agregador '{container_name}' criado com sucesso para o bairro '{bairro}'.")

    except Exception as e:
        print(f"[ERRO] Falha ao criar o agregador '{container_name}': {e}")
