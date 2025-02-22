# utils/aggregator.py

from utils.docker_utils import get_docker_client

def create_aggregator(bairro, image, container_types):

    """
    Cria um agregador para o bairro especificado.

    Args:
        bairro (str): Nome do bairro para o qual o agregador será criado.
        image (str): Imagem Docker a ser usada para o agregador.
        container_types (dict): Dicionário contendo os tipos de contêineres e seus IDs.

    Returns:
        None

    Raises:
        docker.errors.APIError: Caso ocorra um erro ao interagir com a API do Docker.
        docker.errors.ContainerError: Caso o contêiner não seja iniciado corretamente.
        docker.errors.ImageNotFound: Caso a imagem Docker especificada não seja encontrada.
    """

    client = get_docker_client()
    network_name = f"{bairro}_network"
    container_name = f"{bairro}_aggregator"

    try:
        print(f"[INFO] Tentando criar o agregador '{container_name}' na rede '{network_name}'...")

        client.containers.run(
            image,
            name=container_name,
            network=network_name,
            detach=True,
            ports={"22/tcp": 2222},
            environment={"BAIRRO": bairro},
            labels={"type": str(container_types["aggregator"]["id"])},
            extra_hosts={"sftp_host": "192.168.1.124"}
        )
        
        print(f"[SUCESSO] Agregador '{container_name}' criado com sucesso para o bairro '{bairro}'.")

    except Exception as e:
        print(f"[ERRO] Falha ao criar o agregador '{container_name}': {e}")
