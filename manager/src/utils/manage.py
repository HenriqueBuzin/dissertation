# utils/manage.py

from flask import request, redirect, url_for
from .load_balancer import create_load_balancer
from .measurement_nodes import create_measurement_nodes
from .nodes import create_node
from .general import normalize_container_name

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
    
    # Descobre os IDs dos tipos
    lb_id = container_types.get("load_balancer", {}).get("id")
    medidor_id = container_types.get("medidor", {}).get("id")
    nodo_id    = container_types.get("nodo_nevoa", {}).get("id")
    # Se tiver "agregador", aggregator_id = container_types.get("aggregator", {}).get("id") etc.

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
            # Supondo que o LB foi criado como f"{normalize_container_name(bairro)}_load_balancer_1"
            lb_container_name = f"{normalize_container_name(bairro)}_load_balancer_1"
            # A porta interna do LB é 5000 (por convenção do LB).
            lb_url = f"http://{lb_container_name}:5000"

            # Agora chamamos a função create_node, passando lb_url
            create_node(
                bairro=bairro,
                container_name=container_name,   # ex: "nodo_water"
                image=image,
                container_types=container_types,
                load_balancer_url=lb_url,
                quantity=quantity
            )

        # elif container_type == aggregator_id:
        #     create_aggregator(...) # Exemplo

        else:
            print(f"[AVISO] Tipo {container_type} não mapeado para criação.")
        
    return redirect(url_for("manage_containers", bairro=bairro))
