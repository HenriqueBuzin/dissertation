# app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from dotenv import load_dotenv
from utils import (
    group_containers_for_display,
    normalize_container_name,
    get_load_balancer_ports,
    find_display_name_by_id,
    handle_manage_post,
    get_docker_client,
    list_containers,
    load_json,
    save_json
)
import os

load_dotenv()

CONFIG_FILE = os.getenv("CONFIG_FILE")
BAIRROS_MEDIDORES_FILE = os.getenv("BAIRROS_MEDIDORES_FILE")
DOWNLOAD_URLS_FILE = os.getenv("DOWNLOAD_URLS_FILE")
CONTAINER_TYPES_FILE = os.getenv("CONTAINER_TYPES_FILE")

if not all([CONFIG_FILE, BAIRROS_MEDIDORES_FILE, DOWNLOAD_URLS_FILE, CONTAINER_TYPES_FILE]):
    raise ValueError("As variáveis CONFIG_FILE, BAIRROS_MEDIDORES_FILE, DOWNLOAD_URLS_FILE e CONTAINER_TYPES_FILE precisam estar definidas no arquivo .env.")

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

@app.route("/")
def index():
    return redirect(url_for("bairros"))

@app.route("/bairros")
def bairros():
    bairros_data = load_json(BAIRROS_MEDIDORES_FILE, default={})
    return render_template("bairros.html", bairros=bairros_data.keys())

@app.route("/manage/<bairro>", methods=["GET", "POST"])
def manage_containers(bairro):
    """Gerencia os contêineres de um bairro específico."""
    config = load_json(CONFIG_FILE, default={"containers": []})
    container_types = load_json(CONTAINER_TYPES_FILE, default={})
    
    containers = list_containers(filters={"name": normalize_container_name(bairro)})

    load_balancer_http_port, load_balancer_coap_port = get_load_balancer_ports(containers)
    has_load_balancer = (load_balancer_http_port is not None and load_balancer_coap_port is not None)
    
    aggregator_name = f"{bairro}_aggregator"
    has_aggregator = any(c.name == aggregator_name for c in containers)

    lb_id = container_types.get("load_balancer", {}).get("id")
    aggregator_id = container_types.get("aggregator", {}).get("id")

    select_options = []
    for c in config["containers"]:
        ctype_id = c["type"]
        display_name = find_display_name_by_id(container_types, ctype_id)

        # Passo 1: Exibe apenas o Load Balancer caso ele ainda não tenha sido criado
        if not has_load_balancer and ctype_id == lb_id:
            select_options.append({
                "name": c["name"],
                "display_name": display_name
            })

        # Passo 2: Após o Load Balancer ser criado, exibe os outros tipos (incluindo o Agregador)
        if has_load_balancer and ctype_id != lb_id:
            # O Agregador é exibido apenas se ainda não foi criado
            if ctype_id == aggregator_id and not has_aggregator:
                select_options.append({
                    "name": c["name"],
                    "display_name": display_name
                })
            elif ctype_id != aggregator_id:
                # Exibe outros tipos (Nodo de Névoa e Medidor)
                select_options.append({
                    "name": c["name"],
                    "display_name": display_name
                })

    if request.method == "POST":
        return handle_manage_post(
            bairro=bairro,
            config=config,
            container_types=container_types,
            has_load_balancer=has_load_balancer,
            lb_http_port=load_balancer_http_port,
            lb_coap_port=load_balancer_coap_port
        )

    grouped_containers = group_containers_for_display(containers, container_types)

    for group_key, group in grouped_containers.items():
        print(f"[DEBUG] Grupo: {group.get('display_name', 'Sem Nome')} ({group_key})")
        for container in group["containers"]:
            print(f" - {container['name']} (Status: {container['status']})")

    return render_template(
        "manage_containers.html",
        config=config,
        select_options=select_options,
        grouped_containers=grouped_containers,
        bairro=bairro,
        has_load_balancer=has_load_balancer
    )

@app.route("/config_imagens", methods=["GET", "POST"])
def config_imagens():
    config = load_json(CONFIG_FILE, default={"containers": []})
    container_types = load_json(CONTAINER_TYPES_FILE, default={})
    data_mapping = load_json(DOWNLOAD_URLS_FILE, default={})

    if request.method == "POST":
        container_name = request.form.get("name")
        image = request.form.get("image")
        container_type_key = request.form.get("type")
        if container_name and image and container_type_key:
            type_id = container_types[container_type_key]["id"]
            new_container = {
                "name": container_name,
                "image": image,
                "type": type_id,
            }
            config["containers"].append(new_container)
            save_json(CONFIG_FILE, config)
        return redirect(url_for("config_imagens"))

    for c in config["containers"]:
        c["type_display"] = find_display_name_by_id(container_types, c["type"])

    return render_template(
        "config_imagens.html",
        config=config,
        container_types=container_types,
        data_mapping=data_mapping,
    )

@app.route("/config_dados", methods=["GET", "POST"])
def config_dados():
    """Configura os tipos de dados e URLs associadas."""
    data_config = load_json(DOWNLOAD_URLS_FILE, default={})

    if request.method == "POST":
        new_data_id = request.form.get("data_id")
        new_data_url = request.form.get("data_url")

        if new_data_id and new_data_url:
            data_config[new_data_id] = new_data_url
            save_json(DOWNLOAD_URLS_FILE, data_config)

        return redirect(url_for("config_dados"))

    return render_template("config_dados.html", data_config=data_config)

@app.route("/manage_types", methods=["GET", "POST"])
def manage_types():
    """Gerencia os tipos de contêineres disponíveis."""
    container_types = load_json(CONTAINER_TYPES_FILE, default={})

    if request.method == "POST":
        action = request.form.get("action")
        group_key = request.form.get("group_key")
        display_name = request.form.get("display_name")

        if action == "add" and group_key and display_name:
            if group_key not in container_types:
                new_id = max((ct["id"] for ct in container_types.values()), default=0) + 1
                container_types[group_key] = {"id": new_id, "display_name": display_name}
                save_json(CONTAINER_TYPES_FILE, container_types)
        elif action == "delete" and group_key in container_types:
            del container_types[group_key]
            save_json(CONTAINER_TYPES_FILE, container_types)

        return redirect(url_for("manage_types"))

    return render_template("manage_types.html", container_types=container_types)

@app.route("/delete_data_config/<data_id>", methods=["POST"])
def delete_data_config(data_id):
    """Deleta um identificador de dados (data_id)."""
    data_config = load_json(DOWNLOAD_URLS_FILE, default={})

    if data_id in data_config:
        del data_config[data_id]
        save_json(DOWNLOAD_URLS_FILE, data_config)

    return redirect(url_for("config_dados"))

@app.route("/delete_config_imagem/<name>", methods=["POST"])
def delete_config_imagem(name):
    """Deleta uma imagem da configuração."""
    config = load_json(CONFIG_FILE)
    config["containers"] = [c for c in config["containers"] if c["name"] != name]
    save_json(CONFIG_FILE, config)
    return redirect(url_for("config_imagens"))

@app.route("/stop_all/<bairro>", methods=["POST"])
def stop_all(bairro):
    """Para e remove todos os contêineres associados a um bairro."""
    containers = list_containers(filters={"name": normalize_container_name(bairro)})
    for container in containers:
        try:
            if container.status in ["running", "paused"]:
                container.stop()
            container.remove()
            print(f"Contêiner {container.name} removido com sucesso.")
        except Exception as e:
            print(f"Erro ao remover o contêiner {container.name}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/stop_group/<container_type>/<bairro>", methods=["POST"])
def stop_group(container_type, bairro):
    """Para e remove todos os contêineres de um tipo específico em um bairro."""
    if not container_type or container_type == "null":
        print("[ERRO] Tipo de contêiner não fornecido.")
        return "Tipo de contêiner não fornecido.", 400

    containers = list_containers(filters={"label": f"type={container_type}"})
    if not containers:
        print(f"[INFO] Nenhum contêiner encontrado para o tipo {container_type} no bairro {bairro}.")
        return redirect(url_for("manage_containers", bairro=bairro))

    for container in containers:
        try:
            if container.status in ["running", "paused"]:
                container.stop()
            container.remove()
            print(f"[SUCESSO] Contêiner {container.name} do tipo {container_type} removido com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao remover o contêiner {container.name}: {e}")

    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/start_container/<container_id>/<bairro>", methods=["POST"])
def start_container(container_id, bairro):
    """Inicia um contêiner especificado."""
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        if container.status == "paused":
            container.unpause()
        elif container.status == "exited":
            container.start()
        print(f"Contêiner {container.name} iniciado com sucesso.")
    except Exception as e:
        print(f"Erro ao iniciar o contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/pause_container/<container_id>/<bairro>", methods=["POST"])
def pause_container(container_id, bairro):
    """Pausa um contêiner especificado."""
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        if container.status == "running":
            container.pause()
            print(f"Contêiner {container.name} pausado com sucesso.")
        else:
            print(f"Contêiner {container.name} não está em execução.")
    except Exception as e:
        print(f"Erro ao pausar o contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/stop_container/<container_id>/<bairro>", methods=["POST"])
def stop_container(container_id, bairro):
    """Para e remove um contêiner."""
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)

        if container.status in ["running", "paused"]:
            container.stop()
            print(f"Contêiner {container.name} parado com sucesso.")

        container.remove()
        print(f"Contêiner {container.name} removido com sucesso.")
    except Exception as e:
        print(f"Erro ao remover o contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/monitoramento")
def monitoramento():
    """Exibe o monitoramento de um contêiner."""
    container_id = request.args.get("container_id")
    if not container_id:
        return "Container ID não fornecido", 400
    return render_template("monitoramento.html", container_id=container_id)

@socketio.on("get_logs")
def handle_get_logs(data):
    """Obtém os logs do contêiner e envia ao cliente."""
    container_id = data.get("container_id")
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=50).decode("utf-8")
        socketio.emit("log_update", {"container_id": container_id, "logs": logs})
    except Exception as e:
        print(f"Erro ao obter logs do contêiner {container_id}: {e}")
        socketio.emit("log_update", {"container_id": container_id, "logs": "Erro ao obter logs."})

if __name__ == "__main__":
    socketio.run(app, debug=True)
