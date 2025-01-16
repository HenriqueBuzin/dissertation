# app.py

# Importações padrão
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from dotenv import load_dotenv
from utils import (
    create_load_balancer,
    create_measurement_nodes,
    list_containers,
    load_json,
    save_json,
    normalize_container_name,
    group_containers_for_display,
    get_load_balancer_ports,
    get_docker_client
)

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações globais usando .env
CONFIG_FILE = os.getenv("CONFIG_FILE")
BAIRROS_MEDIDORES_FILE = os.getenv("BAIRROS_MEDIDORES_FILE")
DOWNLOAD_URLS_FILE = os.getenv("DOWNLOAD_URLS_FILE")
CONTAINER_TYPES_FILE = os.getenv("CONTAINER_TYPES_FILE")

# Verificação de variáveis essenciais
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

    # Obtém as portas do Load Balancer
    load_balancer_http_port, load_balancer_coap_port = get_load_balancer_ports(containers)
    has_load_balancer = load_balancer_http_port is not None and load_balancer_coap_port is not None

    # Monta as opções para o select
    select_options = [
        {
            "name": container["name"],
            "display_name": next(
                (type_info["display_name"] for key, type_info in container_types.items() if type_info["id"] == container["type"]),
                "Desconhecido"
            )
        }
        for container in config["containers"]
        if (not has_load_balancer and container["type"] == container_types.get("load_balancer", {}).get("id")) or
           (has_load_balancer and container["type"] != container_types.get("load_balancer", {}).get("id"))
    ]

    if request.method == "POST":
        container_name = request.form.get("container_name")
        container_data = next((c for c in config["containers"] if c["name"] == container_name), None)
        container_type = container_data["type"] if container_data else None
        image = container_data["image"] if container_data else None
        quantity = 1 if container_type == container_types.get("load_balancer", {}).get("id") else int(request.form.get("quantity", 1))

        if not image:
            print(f"Imagem não encontrada para {container_name}. Verifique a configuração.")
            return redirect(url_for("manage_containers", bairro=bairro))

        print(f"Iniciando criação do container '{container_name}' com a imagem '{image}'")

        # Criação do Load Balancer
        if container_type == container_types.get("load_balancer", {}).get("id") and not has_load_balancer:
            http_port, coap_port = create_load_balancer(bairro, container_name, image, container_types)
            if http_port and coap_port:
                load_balancer_http_port = http_port
                load_balancer_coap_port = coap_port
                has_load_balancer = True
            else:
                print("Erro ao criar o Load Balancer.")
                return redirect(url_for("manage_containers", bairro=bairro))

        # Criação dos Medidores
        if has_load_balancer:
            create_measurement_nodes(
                bairro, container_name, image, quantity, load_balancer_http_port, load_balancer_coap_port, container_types
            )

        return redirect(url_for("manage_containers", bairro=bairro))

    grouped_containers = group_containers_for_display(containers, container_types)

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
        container_type = request.form.get("type")
        if container_name and image and container_type:
            new_container = {
                "name": container_name,
                "image": image,
                "type": container_type,
            }
            config["containers"].append(new_container)
            save_json(CONFIG_FILE, config)
        return redirect(url_for("config_imagens"))

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
        print("Erro: Tipo de contêiner não fornecido.")
        return "Tipo de contêiner não fornecido.", 400

    containers = list_containers(filters={"label": f"type={container_type}"})
    if not containers:
        print(f"Nenhum contêiner encontrado para o tipo {container_type} no bairro {bairro}.")
        return redirect(url_for("manage_containers", bairro=bairro))

    for container in containers:
        try:
            if container.status in ["running", "paused"]:
                container.stop()
            container.remove()
            print(f"Contêiner {container.name} do tipo {container_type} removido com sucesso.")
        except Exception as e:
            print(f"Erro ao remover o contêiner {container.name}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/start_container/<container_id>/<bairro>", methods=["POST"])
def start_container(container_id, bairro):
    """Inicia um contêiner especificado."""
    client = get_docker_client()  # Obtém o cliente Docker
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
    client = get_docker_client()  # Obtém o cliente Docker
    try:
        container = client.containers.get(container_id)  # Obtém o contêiner
        if container.status == "running":  # Verifica o status do contêiner
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
    client = get_docker_client()  # Obtém o cliente Docker
    try:
        # Obtém o contêiner com base no ID fornecido
        container = client.containers.get(container_id)

        # Verifica o status do contêiner e executa as ações apropriadas
        if container.status in ["running", "paused"]:
            container.stop()
            print(f"Contêiner {container.name} parado com sucesso.")

        # Remove o contêiner
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
    client = get_docker_client()  # Certifique-se de usar o cliente Docker correto
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=50).decode("utf-8")  # Obtém os últimos 50 logs
        socketio.emit("log_update", {"container_id": container_id, "logs": logs})
    except Exception as e:
        print(f"Erro ao obter logs do contêiner {container_id}: {e}")
        socketio.emit("log_update", {"container_id": container_id, "logs": "Erro ao obter logs."})

if __name__ == "__main__":
    socketio.run(app, debug=True)
