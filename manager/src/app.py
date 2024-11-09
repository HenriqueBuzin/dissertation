from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import unicodedata
import socket
import docker
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
client = docker.from_env()

CONFIG_FILE = 'config.json'
BAIRROS_MEDIDORES_FILE = os.path.join(os.getcwd(), 'bairros_medidores.json')
CSV_DOWNLOAD_URL = "https://raw.githubusercontent.com/HenriqueBuzin/dissertation/main/manager/src/data.csv"

CONTAINER_TYPES = {
    "load_balancer": {"id": 1, "display_name": "Load Balancer"},
    "nodo_nevoa": {"id": 2, "display_name": "Nodo de Nevoa"},
    "medidor": {"id": 3, "display_name": "Medidor"}
}

def get_available_port(start_port=5000, end_port=6000):
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def normalize_container_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.replace(" ", "_")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            try:
                return json.load(f) or {"containers": []}
            except json.JSONDecodeError:
                print("Erro ao decodificar config.json, retornando configuração padrão.")
                return {"containers": []}
    return {"containers": []}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Rota inicial que redireciona para a lista de bairros
@app.route("/")
def index():
    return redirect(url_for("bairros"))

# Lista dos bairros
@app.route("/bairros")
def bairros():
    with open('bairros_medidores.json', encoding='utf-8') as f:
        bairros_data = json.load(f)
    bairros = bairros_data.keys()
    return render_template("bairros.html", bairros=bairros)

# Configuração de imagens de contêineres
@app.route("/config_imagens", methods=["GET", "POST"])
def config_imagens():
    config = load_config()
    if request.method == "POST":
        new_name = request.form.get("name")
        new_image = request.form.get("image")
        new_type_str = request.form.get("type")
        new_type_data = CONTAINER_TYPES.get(new_type_str)
        
        if new_name and new_image and new_type_data:
            config["containers"].append({
                "name": new_name,
                "image": new_image,
                "type": new_type_data["id"], 
                "type_name": new_type_data["display_name"]
            })
            save_config(config)
        return redirect(url_for("config_imagens"))
    
    return render_template("config_imagens.html", config=config, CONTAINER_TYPES=CONTAINER_TYPES)

# Gerenciamento de contêineres para um bairro específico
@app.route("/manage/<bairro>", methods=["GET", "POST"])
def manage_containers(bairro):
    config = load_config()
    containers = client.containers.list(all=True, filters={"name": normalize_container_name(bairro)})

    load_balancer_port = None
    has_load_balancer = any(
        container for container in containers
        if container.attrs["Config"]["Labels"].get("type") == str(CONTAINER_TYPES["load_balancer"]["id"])
    )

    if has_load_balancer:
        for container in containers:
            if container.attrs["Config"]["Labels"].get("type") == str(CONTAINER_TYPES["load_balancer"]["id"]):
                load_balancer_port = container.attrs["NetworkSettings"]["Ports"]["5000/tcp"][0]["HostPort"]
                break

    select_options = []
    for item_key, item_data in CONTAINER_TYPES.items():
        if not has_load_balancer and item_data["id"] == CONTAINER_TYPES["load_balancer"]["id"]:
            select_options.append({"name": item_key, "display_name": item_data["display_name"]})
        elif has_load_balancer and item_data["id"] != CONTAINER_TYPES["load_balancer"]["id"]:
            select_options.append({"name": item_key, "display_name": item_data["display_name"]})

    if request.method == "POST":
        container_name = request.form.get("container_name")
        container_data = next((c for c in config["containers"] if c["name"] == container_name), None)
        container_type = container_data["type"] if container_data else None
        image = container_data["image"] if container_data else None
        quantity = 1 if container_type == CONTAINER_TYPES["load_balancer"]["id"] else int(request.form.get("quantity", 1))

        if container_type == CONTAINER_TYPES["load_balancer"]["id"] and has_load_balancer:
            print("Um load balancer já existe para este bairro. Ignorando criação.")
            return redirect(url_for("manage_containers", bairro=bairro))

        if not image:
            print(f"Imagem não encontrada para {container_name}. Verifique a configuração.")
            return redirect(url_for("manage_containers", bairro=bairro))

        print(f"Iniciando criação do container '{container_name}' com a imagem '{image}'")

        if container_type == CONTAINER_TYPES["load_balancer"]["id"] and not has_load_balancer:
            full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"
            
            existing_containers = client.containers.list(all=True, filters={"name": full_container_name})
            if existing_containers:
                for existing_container in existing_containers:
                    print(f"Removendo contêiner existente: {full_container_name}")
                    existing_container.stop()
                    existing_container.remove()
                    print(f"Contêiner {full_container_name} removido com sucesso.")

            try:
                port = get_available_port()
                client.containers.run(
                    image,
                    name=full_container_name,
                    detach=True,
                    environment={"LOAD_BALANCER_PORT": str(port)},
                    ports={"5000/tcp": port},
                    labels={"type": str(container_type)}
                )
                print(f"Load balancer {full_container_name} criado com sucesso na porta {port}.")
                has_load_balancer = True

            except docker.errors.APIError as e:
                print(f"Erro ao criar load balancer {full_container_name}: {e}")
                if "Conflict" in str(e):
                    print(f"Conflito detectado ao criar {full_container_name}. Marcando has_load_balancer como True.")
                    has_load_balancer = True
                else:
                    return redirect(url_for("manage_containers", bairro=bairro))

            containers_after_creation = client.containers.list(all=True, filters={"name": full_container_name})
            if containers_after_creation:
                print(f"Contêiner {full_container_name} está ativo, atualizando has_load_balancer para True.")
                has_load_balancer = True
            else:
                print(f"Contêiner {full_container_name} não foi encontrado após tentativa de criação.")

        if has_load_balancer and load_balancer_port:
            with open(BAIRROS_MEDIDORES_FILE, 'r', encoding='utf-8') as f:
                bairros_data = json.load(f)

            load_balancer_url = f"http://host.docker.internal:{load_balancer_port}/receive_data"
            
            for i in range(quantity):
                unique_node_id = str(i + 1)
                full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{i+1}"

                instance_data = bairros_data.get(bairro, {}).get("nodes", {}).get(unique_node_id, {})

                try:
                    client.containers.run(
                        image,
                        name=full_container_name,
                        detach=True,
                        environment={
                            "HTTP_SERVER_URL": load_balancer_url,
                            "CSV_CONTENTS": CSV_DOWNLOAD_URL,
                            "INSTANCE_DATA": json.dumps(instance_data),
                            "BAIRRO": bairro,
                            "NODE_ID": unique_node_id
                        },
                        labels={"type": str(container_type)}
                    )
                    print(f"Container {full_container_name} criado com sucesso com URL do load balancer: {load_balancer_url}")
                except docker.errors.APIError as e:
                    print(f"Erro ao criar container {full_container_name}: {e}")
                    return redirect(url_for("manage_containers", bairro=bairro))

        return redirect(url_for("manage_containers", bairro=bairro))

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
            "type_name": next((ct["display_name"] for key, ct in CONTAINER_TYPES.items() if str(ct["id"]) == container.attrs["Config"]["Labels"].get("type")), "Desconhecido")
        })

    return render_template(
        "manage_containers.html",
        config=config,
        select_options=select_options,
        grouped_containers=grouped_containers,
        bairro=bairro,
        has_load_balancer=has_load_balancer
    )

# Funções para iniciar, pausar e parar contêineres
@app.route("/start_container/<container_id>/<bairro>", methods=["POST"])
def start_container(container_id, bairro):
    try:
        container = client.containers.get(container_id)
        if container.status == "paused":
            container.unpause()
        else:
            container.start()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    except docker.errors.APIError as e:
        print(f"Erro ao iniciar contêiner {container_id}: {e}")

    return redirect(url_for("manage_containers", bairro=bairro))

# Rota de Monitoramento Específico
@app.route("/monitoramento")
def monitoramento():
    container_id = request.args.get("container_id")
    return render_template("monitoramento.html", container_id=container_id)

# Emitir logs de um contêiner específico
@socketio.on('get_logs')
def handle_get_logs(data):
    container_id = data.get('container_id')
    container = client.containers.get(container_id)
    logs = container.logs(tail=50).decode('utf-8')
    socketio.emit('log_update', {'container_id': container_id, 'logs': logs})

# Pausar contêiner
@app.route("/pause_container/<container_id>/<bairro>", methods=["POST"])
def pause_container(container_id, bairro):
    try:
        container = client.containers.get(container_id)
        if container.status == "running":
            container.pause()
        else:
            print(f"Contêiner {container_id} não está em execução e não pode ser pausado.")
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado. Ignorando.")
    except docker.errors.APIError as e:
        if "is not running" in str(e):
            print(f"Contêiner {container_id} já está pausado. Ignorando.")
        else:
            print(f"Erro ao pausar contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

# Parar contêiner individualmente
@app.route("/stop_container/<container_id>/<bairro>", methods=["POST"])
def stop_container(container_id, bairro):
    try:
        container = client.containers.get(container_id)
        if container.status in ["running", "paused"]:
            container.stop()
        container.remove()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado. Ignorando.")
    except docker.errors.APIError as e:
        if "No such container" in str(e):
            print(f"Contêiner {container_id} já foi removido. Ignorando.")
        else:
            print(f"Erro ao parar contêiner {container_id}: {e}")
    return redirect(url_for("manage_containers", bairro=bairro))

# Parar grupo de contêineres
@app.route("/stop_group/<image_name>/<config_name>/<bairro>", methods=["POST"])
def stop_group(image_name, config_name, bairro):
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

# Parar todos os contêineres
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

# Deletar imagem da configuração
@app.route("/delete_config_imagem/<name>", methods=["POST"])
def delete_config_imagem(name):
    config = load_config()
    config["containers"] = [c for c in config["containers"] if c["name"] != name]
    save_config(config)
    return redirect(url_for("config_imagens"))

if __name__ == "__main__":
    socketio.run(app, debug=True)
