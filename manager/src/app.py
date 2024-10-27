from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import docker
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
client = docker.from_env()

CONFIG_FILE = 'config.json'

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
        if new_name and new_image:
            config["containers"].append({"name": new_name, "image": new_image})
            save_config(config)
        return redirect(url_for("config_imagens"))
    return render_template("config_imagens.html", config=config)

# Gerenciamento de contêineres para um bairro específico
@app.route("/manage/<bairro>", methods=["GET", "POST"])
def manage_containers(bairro):
    config = load_config()
    containers = client.containers.list(all=True, filters={"name": bairro})

    if request.method == "POST":
        container_name = request.form.get("container_name")
        quantity = int(request.form.get("quantity", 1))
        image = next((c["image"] for c in config["containers"] if c["name"] == container_name), None)
        
        if image:
            for i in range(quantity):
                try:
                    full_container_name = f"{bairro}_{container_name}_{i+1}"
                    client.containers.run(image, name=full_container_name, detach=True)
                except docker.errors.APIError as e:
                    print(f"Erro ao criar contêiner {full_container_name}: {e}")
        
        return redirect(url_for("manage_containers", bairro=bairro))

    # Agrupar contêineres por imagem e nome configurado
    grouped_containers = {}
    for container in containers:
        image_name = container.image.tags[0] if container.image.tags else "Sem Imagem"
        config_name = container.name.split('_')[1] if '_' in container.name else container.name

        if image_name not in grouped_containers:
            grouped_containers[image_name] = {}
        if config_name not in grouped_containers[image_name]:
            grouped_containers[image_name][config_name] = []
        
        grouped_containers[image_name][config_name].append(container)

    return render_template("manage_containers.html", config=config, grouped_containers=grouped_containers, bairro=bairro)

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

if __name__ == "__main__":
    socketio.run(app, debug=True)
