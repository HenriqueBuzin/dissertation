# utils/nodes.py

from .docker_utils import client

def create_node(bairro, node_name, image, environment, labels=None):
    """
    Cria um contêiner Docker associado a um bairro específico.

    Args:
        bairro (str): Nome do bairro associado ao contêiner.
        node_name (str): Nome do contêiner a ser criado.
        image (str): Imagem Docker para o contêiner.
        environment (dict): Variáveis de ambiente para configurar o contêiner.
        labels (dict, optional): Labels adicionais para o contêiner.

    Raises:
        docker.errors.APIError: Se ocorrer algum problema na criação do contêiner.
    """
    # Define o nome da rede associada ao bairro
    network_name = f"{bairro}_network"

    try:
        # Tenta criar o contêiner
        client.containers.run(
            image=image,
            name=node_name,
            network=network_name,
            detach=True,
            environment=environment,
            labels=labels if labels else {}  # Adiciona os labels, se fornecidos
        )
        print(f"[SUCESSO] Nó {node_name} criado na rede {network_name}.")
    except Exception as e:
        print(f"[ERRO] Falha ao criar o nó {node_name} na rede {network_name}: {e}")
