# utils/container_display.py

def group_containers_for_display(containers, container_types):
    grouped_containers = {}
    for container in containers:
        container_type_id = container.attrs.get("Config", {}).get("Labels", {}).get("type")
        type_name = container_types.get(container_type_id, {}).get("display_name", "Desconhecido")
        if container_type_id not in grouped_containers:
            grouped_containers[container_type_id] = {"display_name": type_name, "containers": []}
        grouped_containers[container_type_id]["containers"].append(
            {
                "id": container.id,
                "short_id": container.short_id,
                "name": container.name,
                "status": container.status,
            }
        )
    return grouped_containers
