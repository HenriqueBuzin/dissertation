# utils/container_display.py

def group_containers_for_display(containers, container_types):
    grouped_containers = {}

    # reverse_map: "1" -> {"key": "load_balancer", "display_name": "Load Balancer"}
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
            # Em vez de group_key ser a *string* "medidor", use o *próprio ID*:
            group_key = label_id  # "2"
            display_name = reverse_map[label_id]["display_name"]  # "Medidor"
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
    """Busca o display_name cujo 'id' seja igual a type_id (numérico)."""
    for key, info in container_types.items():
        if info["id"] == type_id:
            return info["display_name"]
    return "Desconhecido"
