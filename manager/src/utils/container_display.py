# utils/container_display.py

def group_containers_for_display(containers, container_types):
    
    """
    Agrupa contêineres para exibição com base em seus tipos.

    Args:
        containers (list): Lista de objetos de contêineres Docker.
        container_types (dict): Dicionário mapeando os tipos de contêineres e suas informações.

    Returns:
        dict: Um dicionário onde cada grupo de contêineres é identificado por um tipo, com seus dados organizados.
    """

    grouped_containers = {}

    reverse_map = {}
    for container_type_key, type_info in container_types.items():
        str_id = str(type_info["id"])
        reverse_map[str_id] = {
            "key": container_type_key,
            "display_name": type_info["display_name"]
        }

    for container in containers:
        label_id = container.attrs.get("Config", {}).get("Labels", {}).get("type", "")
        
        if label_id in reverse_map:
            group_key = label_id
            display_name = reverse_map[label_id]["display_name"]
        else:
            group_key = "desconhecido"
            display_name = "Desconhecido"

        if group_key not in grouped_containers:
            grouped_containers[group_key] = {
                "display_name": display_name,
                "containers": []
            }
        grouped_containers[group_key]["containers"].append({
            "id": container.id,
            "name": container.name,
            "status": container.status,
            "short_id": container.short_id
        })
    
    return grouped_containers

def find_display_name_by_id(container_types, type_id):

    """
    Busca o nome de exibição (`display_name`) de um tipo de contêiner com base em seu ID.

    Args:
        container_types (dict): Dicionário com os tipos de contêineres e suas informações.
        type_id (int): ID do tipo de contêiner.

    Returns:
        str: Nome de exibição correspondente ao ID, ou "Desconhecido" se não encontrado.
    """
     
    for key, info in container_types.items():
        if info["id"] == type_id:
            return info["display_name"]
    return "Desconhecido"
