# utils/manage.py

from flask import request, redirect, url_for
from .load_balancer import create_load_balancer
from .measurement_nodes import create_measurement_nodes
from .docker_utils import list_containers
from .network import get_load_balancer_ports
# ... e o que mais você precisar

def handle_manage_post(
    bairro,
    config,
    container_types,
    has_load_balancer,
    lb_http_port,
    lb_coap_port
):
    """
    Lida com o formulário POST enviado em /manage/<bairro>.
    Decide se cria LB, medidores, nós, agregadores etc.
    """
    container_name = request.form.get("container_name")
    container_data = next(
        (c for c in config["containers"] if c["name"] == container_name), 
        None
    )
    if not container_data:
        print("[ERRO] Não encontrou a config para esse contêiner")
        return redirect(url_for("manage_containers", bairro=bairro))
    
    container_type = container_data["type"]
    image = container_data["image"]
    
    # Descobre o ID do LB
    lb_id = container_types.get("load_balancer", {}).get("id")
    
    # Pega a quantidade (se for LB, forçamos 1)
    quantity = 1 if container_type == lb_id else int(request.form.get("quantity", 1))

    # Caso falte a imagem
    if not image:
        print(f"[ERRO] Imagem não encontrada para o contêiner '{container_name}'.")
        return redirect(url_for("manage_containers", bairro=bairro))

    print(f"[INFO] Iniciando criação do contêiner '{container_name}' (type={container_type}).")

    # --- 1) LOAD BALANCER ---
    if container_type == lb_id and not has_load_balancer:
        http_port, coap_port = create_load_balancer(bairro, container_name, image, container_types)
        if not (http_port and coap_port):
            print("[ERRO] Falha ao criar o LB")
        return redirect(url_for("manage_containers", bairro=bairro))
    
    # Se já existe LB, vamos ver o que mais precisa criar
    if has_load_balancer and container_type != lb_id:
        # Observação: aqui você pode criar um dicionário de handlers se quiser
        # Por exemplo: handlers = { medidor_id: create_measurement_nodes, nodo_id: create_fog_node, etc. }
        # E então chamaria: handlers[container_type](...)
        # Mas por simplicidade, use if/elif/else:
        
        medidor_id = container_types.get("medidor", {}).get("id")
        nodo_id    = container_types.get("nodo_nevoa", {}).get("id")
        # Se tiver "agregador", aggregator_id = container_types.get("aggregator", {}).get("id") etc.

        if container_type == medidor_id:
            create_measurement_nodes(
                bairro, 
                container_name, 
                image, 
                quantity,
                lb_http_port, 
                lb_coap_port, 
                container_types
            )

        elif container_type == nodo_id:
            # Chamar algo como create_fog_nodes(...) 
            # ou sua função create_node(...) + environment para "nodo_nevoa"
            pass

        # elif container_type == aggregator_id:
        #     create_aggregator(...) # Exemplo

        else:
            print(f"[AVISO] Tipo {container_type} não mapeado para criação.")
        
    return redirect(url_for("manage_containers", bairro=bairro))
