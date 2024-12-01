# Importações padrão
import os
import json

# Importações de terceiros
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import docker
from urllib.parse import unquote

# Importações locais
from utils import (
    get_available_port,
    normalize_container_name,
    load_config,
    save_config
)

# Configurações e constantes globais
BASE_PATH = os.getcwd()  # Diretório base
JSON_PATH = os.path.join(BASE_PATH, 'jsons')  # Caminho para a pasta JSONs

CONFIG_FILE = os.path.join(JSON_PATH, 'config.json')
BAIRROS_MEDIDORES_FILE = os.path.join(JSON_PATH, 'bairros_medidores.json')
DOWNLOAD_URLS_FILE = os.path.join(JSON_PATH, 'download_urls.json')
CONTAINER_TYPES_FILE = os.path.join(JSON_PATH, 'container_types.json')

# Inicialização do Flask e SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Cliente Docker
client = docker.from_env()

# === ROTAS DE NAVEGAÇÃO ===

@app.route("/")
def index():
    """Redireciona para a lista de bairros."""
    return redirect(url_for("bairros"))

@app.route("/bairros")
def bairros():
    """Exibe a lista de bairros disponíveis."""
    if os.path.exists(BAIRROS_MEDIDORES_FILE):
        with open(BAIRROS_MEDIDORES_FILE, 'r', encoding='utf-8') as f:
            bairros_data = json.load(f)
        bairros = bairros_data.keys()
        return render_template("bairros.html", bairros=bairros)
    print("Erro: Arquivo bairros_medidores.json não encontrado.")
    return render_template("bairros.html", bairros=[])

# === ROTAS DE CONFIGURAÇÃO ===

@app.route("/delete_config_imagem/<name>", methods=["POST"])
def delete_config_imagem(name):
    """Deleta uma imagem da configuração."""
    config = load_config()
    config["containers"] = [c for c in config["containers"] if c["name"] != name]
    save_config(config)
    return redirect(url_for("config_imagens"))

@app.route("/config_dados", methods=["GET", "POST"])
def config_dados():
    """Configura os tipos de dados e URLs associadas."""
    data_config = load_download_urls()

    if request.method == "POST":
        new_data_id = request.form.get("data_id")
        new_data_url = request.form.get("data_url")

        if new_data_id and new_data_url:
            data_config[new_data_id] = new_data_url
            save_download_urls(data_config)

        return redirect(url_for("config_dados"))

    return render_template("config_dados.html", data_config=data_config)

@app.route("/delete_data_config/<data_id>", methods=["POST"])
def delete_data_config(data_id):
    """Deleta um identificador de dados (data_id)."""
    data_config = load_download_urls()

    if data_id in data_config:
        del data_config[data_id]
        save_download_urls(data_config)

    return redirect(url_for("config_dados"))

@app.route("/config_imagens", methods=["GET", "POST"])
def config_imagens():
    config = load_config()
    data_mapping = load_download_urls()
    container_types = load_container_types()

    # Mapear os tipos diretamente no backend
    for container in config["containers"]:
        container["type_display"] = None  # Inicializa com None
        container["type"] = int(container["type"]) if isinstance(container["type"], (str, float)) else container["type"]
        # Busca pelo display_name correspondente
        for key, type_info in container_types.items():
            if type_info["id"] == container["type"]:
                container["type_display"] = type_info["display_name"]  # Agora usa o display_name

    if request.method == "POST":
        new_name = request.form.get("name")
        new_image = request.form.get("image")
        new_type_key = request.form.get("type")
        data_id = request.form.get("data_id")

        if new_type_key not in container_types:
            print(f"Erro: Tipo de contêiner '{new_type_key}' não encontrado.")
            return redirect(url_for("config_imagens"))

        new_type_data = container_types[new_type_key]

        container_config = {
            "name": new_name,
            "image": new_image,
            "type": new_type_data["id"]
        }

        if new_type_key == "medidor" and data_id:
            container_config["data_id"] = data_id

        config["containers"].append(container_config)
        save_config(config)

        return redirect(url_for("config_imagens"))

    return render_template(
        "config_imagens.html",
        config=config,
        container_types=container_types,
        data_mapping=data_mapping
    )

def load_download_urls():
    """Carrega as URLs de download associadas aos identificadores de dados."""
    if os.path.exists(DOWNLOAD_URLS_FILE):
        with open(DOWNLOAD_URLS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Erro ao decodificar download_urls.json. Retornando dicionário vazio.")
                return {}
    print("Arquivo download_urls.json não encontrado. Retornando dicionário vazio.")
    return {}

# === ROTAS DE GERENCIAMENTO DE CONTÊINERES ===

@app.route("/manage_types", methods=["GET", "POST"])
def manage_types():
    container_types = load_container_types()

    if request.method == "POST":
        action = request.form.get("action")
        group_key = request.form.get("group_key")
        display_name = request.form.get("display_name")

        if action == "add" and group_key and display_name:
            if group_key not in container_types:
                new_id = max((ct["id"] for ct in container_types.values()), default=0) + 1
                container_types[group_key] = {
                    "id": new_id,
                    "display_name": display_name,
                }
                save_container_types(container_types)
        elif action == "delete" and group_key in container_types:
            del container_types[group_key]
            save_container_types(container_types)

        return redirect(url_for("manage_types"))

    return render_template("manage_types.html", container_types=container_types)

@app.route("/manage/<bairro>", methods=["GET", "POST"])
def manage_containers(bairro):
    """Gerencia os contêineres de um bairro específico."""
    config = load_config()
    container_types = load_container_types()  # Carrega os tipos de contêineres do JSON
    containers = client.containers.list(all=True, filters={"name": normalize_container_name(bairro)})

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

    grouped_containers = group_containers_for_display(containers)

    return render_template(
        "manage_containers.html",
        config=config,
        select_options=select_options,
        grouped_containers=grouped_containers,
        bairro=bairro,
        has_load_balancer=has_load_balancer
    )

# === ROTAS DE CONTROLE DE CONTÊINERES ===

@socketio.on('get_logs')
def handle_get_logs(data):
    container_id = data.get('container_id')
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=50).decode('utf-8')
        socketio.emit('log_update', {'container_id': container_id, 'logs': logs})
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado para logs.")
        socketio.emit('log_update', {'container_id': container_id, 'logs': 'Erro: Contêiner não encontrado.'})

@app.route("/monitoramento")
def monitoramento():
    container_id = request.args.get("container_id")
    return render_template("monitoramento.html", container_id=container_id)

@app.route("/pause_container/<container_id>/<bairro>", methods=["POST"])
def pause_container(container_id, bairro):
    """Pausa um contêiner."""
    try:
        container = client.containers.get(container_id)
        if container.status == "running":
            container.pause()
            print(f"Contêiner {container.name} pausado com sucesso.")
        else:
            print(f"Contêiner {container.name} não está em execução.")
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    except docker.errors.APIError as e:
        print(f"Erro ao pausar o contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/stop_group/<image_name>/<config_name>/<bairro>", methods=["POST"])
def stop_group(image_name, config_name, bairro):
    image_name = unquote(image_name)
    containers = client.containers.list(all=True)

    for container in containers:
        if container.image.tags and container.image.tags[0] == image_name and config_name in container.name:
            try:
                if container.status in ["running", "paused"]:
                    container.stop()
                container.remove()
            except docker.errors.NotFound:
                print(f"Contêiner {container.name} já foi removido.")
            except docker.errors.APIError as e:
                if "No such container" in str(e):
                    print(f"Contêiner {container.name} já foi removido. Ignorando.")
                else:
                    print(f"Erro ao parar contêiner {container.name}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/stop_all/<bairro>", methods=["POST"])
def stop_all(bairro):
    containers = client.containers.list(all=True)
    for container in containers:
        try:
            if container.status in ["running", "paused"]:
                container.stop()
            container.remove()
        except docker.errors.NotFound:
            print(f"Contêiner {container.name} já foi removido.")
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                print(f"Contêiner {container.name} já foi removido. Ignorando.")
            else:
                print(f"Erro ao parar contêiner {container.name}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/start_container/<container_id>/<bairro>", methods=["POST"])
def start_container(container_id, bairro):
    """Inicia um contêiner."""
    try:
        container = client.containers.get(container_id)
        if container.status == "paused":
            container.unpause()
        else:
            container.start()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    return redirect(url_for("manage_containers", bairro=bairro))

@app.route("/stop_container/<container_id>/<bairro>", methods=["POST"])
def stop_container(container_id, bairro):
    """Para e remove um contêiner."""
    try:
        container = client.containers.get(container_id)
        if container.status in ["running", "paused"]:
            container.stop()
        container.remove()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    return redirect(url_for("manage_containers", bairro=bairro))

# === FUNÇÕES AUXILIARES ===

def get_load_balancer_port(containers):
    """Obtém a porta do Load Balancer de um dos contêineres."""
    for container in containers:
        try:
            ports = container.attrs["NetworkSettings"]["Ports"]
            if ports and "5000/tcp" in ports and ports["5000/tcp"]:
                return ports["5000/tcp"][0]["HostPort"]
        except (KeyError, TypeError):
            continue
    print("Erro: Porta do Load Balancer não encontrada.")
    return None

def group_containers_for_display(containers):
    """Agrupa os contêineres para exibição na interface."""
    container_types = load_container_types()  # Carrega os tipos de contêineres do JSON
    grouped_containers = {}

    for container in containers:
        image_name = container.image.tags[0] if container.image.tags else "Sem Imagem"
        config_name = container.name.split('_')[1] if '_' in container.name else container.name

        if image_name not in grouped_containers:
            grouped_containers[image_name] = {}
        if config_name not in grouped_containers[image_name]:
            grouped_containers[image_name][config_name] = []

        grouped_containers[image_name][config_name].append({
            "container": container,
            "type_name": next(
                (type_info["display_name"] for key, type_info in container_types.items()
                 if str(type_info["id"]) == container.attrs["Config"]["Labels"].get("type", "")),
                "Desconhecido"
            )
        })
    return grouped_containers

def create_load_balancer(bairro, container_name, image, container_types):
    """Cria o Load Balancer com suporte a HTTP e CoAP."""
    try:
        # Obter portas disponíveis
        http_port = get_available_port()
        coap_port = get_available_port(http_port + 1)  # Porta subsequente para evitar conflitos

        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"

        # Remover contêineres antigos com o mesmo nome, se existirem
        existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
        for container in existing_containers:
            print(f"Removendo contêiner antigo: {full_container_name}")
            container.stop()
            container.remove()

        # Criar o Load Balancer com ambas as portas
        client.containers.run(
            image,
            name=full_container_name,
            detach=True,
            environment={
                "LOAD_BALANCER_HTTP_PORT": str(http_port),
                "LOAD_BALANCER_COAP_PORT": str(coap_port)
            },
            ports={
                "5000/tcp": http_port,    # Porta HTTP
                "5683/udp": coap_port     # Porta CoAP
            },
            labels={"type": str(container_types["load_balancer"]["id"])}
        )
        print(f"Load Balancer criado com sucesso. HTTP: {http_port}, CoAP: {coap_port}.")
        return http_port, coap_port
    except docker.errors.APIError as e:
        print(f"Erro ao criar Load Balancer: {e}")
        return None, None

def create_measurement_nodes(bairro, container_name, image, quantity, load_balancer_http_port, load_balancer_coap_port, container_types):
    """Cria os nós de medição."""
    with open(BAIRROS_MEDIDORES_FILE, 'r', encoding='utf-8') as f:
        bairros_data = json.load(f)

    # Carregar o mapeamento de URLs
    data_urls = load_download_urls()

    # URLs do Load Balancer para HTTP e CoAP
    load_balancer_http_url = f"http://host.docker.internal:{load_balancer_http_port}/receive_data"
    load_balancer_coap_url = f"coap://host.docker.internal:{load_balancer_coap_port}/receive_data"

    for i in range(quantity):
        unique_node_id = str(i + 1)
        full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{i+1}"
        instance_data = bairros_data.get(bairro, {}).get("nodes", {}).get(unique_node_id, {})

        # Encontra o identificador de dados no container config
        container_data = next((c for c in load_config()["containers"] if c["name"] == container_name), None)
        data_id = container_data.get("data_id") if container_data else None
        download_url = data_urls.get(data_id)

        if not download_url:
            print(f"Erro: Nenhuma URL encontrada para o identificador de dados '{data_id}' no medidor '{container_name}'.")
            continue

        try:
            client.containers.run(
                image,
                name=full_container_name,
                detach=True,
                environment={
                    "HTTP_SERVER_URL": load_balancer_http_url,
                    "COAP_SERVER_URL": load_balancer_coap_url,
                    "CSV_URL": download_url,
                    "INSTANCE_DATA": json.dumps(instance_data),
                    "BAIRRO": bairro,
                    "NODE_ID": unique_node_id
                },
                labels={"type": str(container_types["medidor"]["id"])}
            )
            print(f"Medidor {full_container_name} criado com sucesso com URLs HTTP e CoAP.")
        except docker.errors.APIError as e:
            print(f"Erro ao criar medidor {full_container_name}: {e}")
            
def get_load_balancer_ports(containers):
    """Obtém as portas HTTP e CoAP do Load Balancer de um dos contêineres."""
    for container in containers:
        try:
            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            http_port = ports.get("5000/tcp", [{}])[0].get("HostPort")
            coap_port = ports.get("5683/udp", [{}])[0].get("HostPort")

            if http_port and coap_port:
                return http_port, coap_port
        except (KeyError, TypeError, IndexError):
            continue
    print("Erro: Portas do Load Balancer não encontradas.")
    return None, None

def save_download_urls(data):
    """Salva as URLs de download associadas aos identificadores de dados."""
    with open(DOWNLOAD_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_container_types():
    """Carrega os tipos de contêineres do arquivo JSON."""
    if os.path.exists(CONTAINER_TYPES_FILE):
        try:
            with open(CONTAINER_TYPES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Erro: Arquivo {CONTAINER_TYPES_FILE} está corrompido.")
    return {}

def save_container_types(data):
    """Salva os tipos de contêineres no arquivo JSON."""
    with open(CONTAINER_TYPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# === INICIALIZAÇÃO DA APLICAÇÃO ===

if __name__ == "__main__":
    socketio.run(app, debug=True)
