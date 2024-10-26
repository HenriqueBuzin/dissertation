from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import docker
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
client = docker.from_env()

CONFIG_FILE = 'config.json'

# Funções para carregar e salvar configurações
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"containers": []}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def index():
    config = load_config()
    if request.method == "POST":
        container_name = request.form.get("container_name")
        quantity = int(request.form.get("quantity", 1))
        image = next((c["image"] for c in config["containers"] if c["name"] == container_name), None)

        if image:
            for i in range(quantity):
                try:
                    full_container_name = f"{container_name}_{i+1}"
                    client.containers.run(image, name=full_container_name, detach=True)
                except docker.errors.APIError as e:
                    print(f"Erro ao criar contêiner {full_container_name}: {e}")
        return redirect(url_for("index"))

    containers = client.containers.list(all=True)
    service_containers = {}
    for container in containers:
        service_name = container.name.split('_')[0]
        if service_name not in service_containers:
            service_containers[service_name] = []
        service_containers[service_name].append(container)

    return render_template("index.html", config=config, service_containers=service_containers)

# Endpoint para iniciar um contêiner
@app.route("/start_container/<container_id>", methods=["POST"])
def start_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.start()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    return redirect(url_for("index"))

# Endpoint para pausar um contêiner
@app.route("/pause_container/<container_id>", methods=["POST"])
def pause_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.pause()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    return redirect(url_for("index"))

# Endpoint para parar um contêiner
@app.route("/stop_container/<container_id>", methods=["POST"])
def stop_container(container_id):
    try:
        container = client.containers.get(container_id)
        container.stop()
    except docker.errors.NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    return redirect(url_for("index"))

# Endpoint para ver logs de um contêiner
@app.route("/logs/<container_id>")
def logs(container_id):
    container = client.containers.get(container_id)
    log_output = container.logs(tail=50).decode("utf-8")  # Últimos 50 logs
    return jsonify({"logs": log_output})

@app.route("/manage", methods=["GET", "POST"])
def manage():
    config = load_config()
    if request.method == "POST":
        new_name = request.form.get("name")
        new_image = request.form.get("image")
        if new_name and new_image:
            config["containers"].append({"name": new_name, "image": new_image})
            save_config(config)
        return redirect(url_for("manage"))
    return render_template("manage.html", config=config)

@app.route("/delete_config/<name>", methods=["GET"])
def delete_config(name):
    config = load_config()
    config["containers"] = [c for c in config["containers"] if c["name"] != name]
    save_config(config)
    return redirect(url_for("manage"))

if __name__ == "__main__":
    socketio.run(app, debug=True)
