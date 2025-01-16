# utils/aggregator.py

def create_aggregator(bairro, image):
    """Cria o agregador para um bairro."""
    network_name = f"{bairro}_network"
    container_name = f"{bairro}_aggregator"
    client.containers.run(
        image,
        name=container_name,
        network=network_name,
        detach=True,
        ports={"8000/tcp": None},
        environment={"BAIRRO": bairro}
    )
    print(f"Agregador criado para o bairro '{bairro}'.")
