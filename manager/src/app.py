from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import unicodedata
import tempfile
import socket
import docker
import json
import csv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
client = docker.from_env()

CONFIG_FILE = 'config.json'

CONTAINER_TYPES = {
    "load_balancer": 1,
    "nodo_nevoa": 2,
    "medidor": 3
}

CSV_FILE_PATH = os.path.join(os.getcwd(), 'data.csv')
BAIRROS_MEDIDORES_FILE = os.path.join(os.getcwd(), 'bairros_medidores.json')

def load_bairro_data(bairro):
    if os.path.exists(BAIRROS_MEDIDORES_FILE):
        with open(BAIRROS_MEDIDORES_FILE, encoding='utf-8') as f:
            bairros_data = json.load(f)
        return bairros_data.get(bairro, {}).get("nodes", {})
    return {}

def create_instance_data_file(bairro, instance_id, instance_data):
    """Cria um arquivo temporário para armazenar dados específicos de cada medidor."""
    temp_dir = os.path.join(tempfile.gettempdir(), 'medidores', bairro)
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"instance_{instance_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(instance_data, f)
    return file_path

def load_csv_data(file_path):
    data = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            data.append(row)
    return data

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
            return json.load(f)
    return {"containers": []}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

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
        new_type = CONTAINER_TYPES.get(new_type_str)
        if new_name and new_image:
            config["containers"].append({"name": new_name, "image": new_image, "type": new_type})
            save_config(config)
        return redirect(url_for("config_imagens"))
    return render_template("config_imagens.html", config=config)

# Gerenciamento de contêineres para um bairro específico
@app.route("/manage/<bairro>", methods=["GET", "POST"])
def manage_containers(bairro):
    config = load_config()
    containers = client.containers.list(all=True, filters={"name": normalize_container_name(bairro)})

    # Verificar se já existe um load_balancer e capturar a porta dele
    load_balancer_port = None
    has_load_balancer = any(
        container for container in containers
        if container.attrs["Config"]["Labels"].get("type") == str(CONTAINER_TYPES["load_balancer"])
    )

    # Se tiver um load balancer, captura a porta dele
    if has_load_balancer:
        for container in containers:
            if container.attrs["Config"]["Labels"].get("type") == str(CONTAINER_TYPES["load_balancer"]):
                load_balancer_port = container.attrs["NetworkSettings"]["Ports"]["5000/tcp"][0]["HostPort"]
                break

    select_options = []
    for item in config["containers"]:
        if not has_load_balancer and item["type"] == CONTAINER_TYPES["load_balancer"]:
            select_options.append(item)
        elif has_load_balancer and item["type"] != CONTAINER_TYPES["load_balancer"]:
            select_options.append(item)

    if request.method == "POST":
        container_name = request.form.get("container_name")
        container_type = next((c["type"] for c in config["containers"] if c["name"] == container_name), None)
        image = next((c["image"] for c in config["containers"] if c["name"] == container_name), None)
        quantity = 1 if container_type == CONTAINER_TYPES["load_balancer"] else int(request.form.get("quantity", 1))

        # Verifica se já existe um load balancer e impede a criação de mais de um
        if container_type == CONTAINER_TYPES["load_balancer"] and has_load_balancer:
            print("Um load balancer já existe para este bairro. Ignorando criação.")
            return redirect(url_for("manage_containers", bairro=bairro))

        # Verifica se a imagem foi encontrada
        if not image:
            print(f"Imagem não encontrada para {container_name}. Verifique a configuração.")
            return redirect(url_for("manage_containers", bairro=bairro))

        print(f"Iniciando criação do container '{container_name}' com a imagem '{image}'")

        if container_type == CONTAINER_TYPES["load_balancer"] and not has_load_balancer:
            port = get_available_port()
            load_balancer_port = port
            print(f"Iniciando criação do load balancer '{container_name}' na porta {port} com imagem '{image}'")
            full_container_name = f"{normalize_container_name(bairro)}_{container_name}_1"
            try:
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
                return redirect(url_for("manage_containers", bairro=bairro))
        # No trecho que cria os contêineres de medidor no app.py
        if has_load_balancer and load_balancer_port:
            with open(BAIRROS_MEDIDORES_FILE, 'r', encoding='utf-8') as f:
                bairros_data = json.load(f)  # Carrega todo o JSON

            # Carrega o conteúdo do CSV como uma lista de dicionários
            csv_data = load_csv_data(CSV_FILE_PATH)
            load_balancer_url = f"http://host.docker.internal:{load_balancer_port}/receive_data"
            
            for i in range(quantity):
                unique_node_id = str(i + 1)
                full_container_name = f"{normalize_container_name(bairro)}_{container_name}_{i+1}"

                # Extrai apenas os dados do bairro e do nó específico
                instance_data = bairros_data.get(bairro, {}).get("nodes", {}).get(unique_node_id, {})

                print(csv_data)
                print(11111111111111111111111111111)

                try:
                    client.containers.run(
                        image,
                        name=full_container_name,
                        detach=True,
                        environment={
                            "HTTP_SERVER_URL": load_balancer_url,
                            "CSV_CONTENTS": json.dumps(csv_data),  # Passa o conteúdo do CSV diretamente
                            "INSTANCE_DATA": json.dumps(instance_data),  # Passa apenas os dados específicos do `INSTANCE_DATA`
                            "BAIRRO": bairro,  # Identificador do bairro específico
                            "NODE_ID": unique_node_id  # ID único do medidor
                        },
                        labels={"type": str(container_type)}
                    )
                    print(f"Container {full_container_name} criado com sucesso com URL do load balancer: {load_balancer_url}")
                except docker.errors.APIError as e:
                    print(f"Erro ao criar container {full_container_name}: {e}")
                    return redirect(url_for("manage_containers", bairro=bairro))

        return redirect(url_for("manage_containers", bairro=bairro))

    # Agrupa contêineres por imagem e nome configurado
    grouped_containers = {}
    for container in containers:
        image_name = container.image.tags[0] if container.image.tags else "Sem Imagem"
        config_name = container.name.split('_')[1] if '_' in container.name else container.name

        if image_name not in grouped_containers:
            grouped_containers[image_name] = {}
        if config_name not in grouped_containers[image_name]:
            grouped_containers[image_name][config_name] = []

        grouped_containers[image_name][config_name].append(container)

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
            container.unpause()  # Despausa, se está pausado
        else:
            container.start()  # Caso contrário, inicia normalmente
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
    logs = container.logs(tail=50).decode('utf-8')  # Pega os últimos 50 registros
    socketio.emit('log_update', {'container_id': container_id, 'logs': logs})

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

@app.route("/delete_config_imagem/<name>", methods=["POST"])
def delete_config_imagem(name):
    config = load_config()
    # Filtra a configuração removendo a que tem o nome correspondente
    config["containers"] = [c for c in config["containers"] if c["name"] != name]
    save_config(config)
    return redirect(url_for("config_imagens"))

if __name__ == "__main__":
    socketio.run(app, debug=True)
