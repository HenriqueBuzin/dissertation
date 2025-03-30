# utils/manage.py

from .measurement_nodes import create_measurement_nodes
from .load_balancer import create_load_balancer
from .general import normalize_container_name
from flask import request, redirect, url_for
from .aggregator import create_aggregator
from .nodes import create_node

ALL_LOAD_BALANCERS = []

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
    Decide a criação de diferentes tipos de contêineres, incluindo Load Balancer, medidores e nós.

    Args:
        bairro (str): Nome do bairro em que as ações serão executadas.
        config (dict): Configurações carregadas do arquivo de configuração (geralmente `config.json`).
        container_types (dict): Tipos de contêineres e seus respectivos IDs.
        has_load_balancer (bool): Indica se o Load Balancer já foi criado para o bairro.
        lb_http_port (int): Porta HTTP do Load Balancer.
        lb_coap_port (int): Porta CoAP do Load Balancer.

    Returns:
        flask.Response: Redireciona para a página de gerenciamento de contêineres do bairro.
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
    
    lb_id = container_types.get("load_balancer", {}).get("id")
    medidor_id = container_types.get("medidor", {}).get("id")
    nodo_id    = container_types.get("nodo_nevoa", {}).get("id")
    aggregator_id = container_types.get("aggregator", {}).get("id")

    quantity = 1 if container_type == lb_id else int(request.form.get("quantity", 1))

    if not image:
        print(f"[ERRO] Imagem não encontrada para o contêiner '{container_name}'.")
        return redirect(url_for("manage_containers", bairro=bairro))

    print(f"[INFO] Iniciando criação do contêiner '{container_name}' (type={container_type}).")

    if container_type == lb_id and not has_load_balancer:
        
        peers = ALL_LOAD_BALANCERS
        
        http_port, coap_port = create_load_balancer(bairro, container_name, image, container_types, peers=peers)
        
        if not (http_port and coap_port):
            print("[ERRO] Falha ao criar o LB")
        else: 
            new_lb_name = f"{normalize_container_name(bairro)}_{container_name}_1"
            ALL_LOAD_BALANCERS.append(new_lb_name)
        
        return redirect(url_for("manage_containers", bairro=bairro))
    
    if has_load_balancer and container_type != lb_id:
        
        if container_type == medidor_id:
            create_measurement_nodes(
                bairro, 
                container_name, 
                image, 
                quantity,
                lb_http_port, 
                lb_coap_port
            )
            
        elif container_type == nodo_id:
            lb_container_name = f"{normalize_container_name(bairro)}_load_balancer_1"
            lb_url = f"http://{lb_container_name}:5000"

            create_node(
                bairro=bairro,
                container_name=container_name,
                image=image,
                container_types=container_types,
                load_balancer_url=lb_url,
                quantity=quantity
            )

        elif container_type == aggregator_id:
            create_aggregator(
                bairro=bairro, 
                image=image,
                container_types=container_types
            )

        else:
            print(f"[AVISO] Tipo {container_type} não mapeado para criação.")
        
    return redirect(url_for("manage_containers", bairro=bairro))
