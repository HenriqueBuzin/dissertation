import threading
import docker
import time
import os

stop_threads = False  # Flag to signal threads to stop

def monitor_container_logs(container, container_number):
    """Monitora os logs de um contêiner específico."""
    global stop_threads
    for line in container.logs(stream=True):
        if stop_threads:
            break
        print(f"Container {container_number}: {line.decode('utf-8').strip()}\n")

def create_replicas(num_replicas):
    client = docker.from_env()
    containers = []

    for i in range(1, num_replicas + 1):
        try:
            container_name = f"medidor-{i}"
            environment = {"REPLICANUMBER": str(i)}
            container = client.containers.run("medidor", name=container_name, detach=True, environment=environment)
            containers.append(container)
        except Exception as e:
            print(f"Error starting container: {e}")

    threads = []
    for i, container in enumerate(containers, start=1):
        thread = threading.Thread(target=monitor_container_logs, args=(container, i), daemon=True)
        thread.start()
        threads.append(thread)

    return threads, containers

def stop_and_remove_containers():
    client = docker.from_env()
    all_containers = client.containers.list(all=True)
    for container in all_containers:
        if any(name.startswith("/medidor-") for name in container.names):
            try:
                container.stop()
                container.remove()
                print(f"Container {container.name} stopped and removed.")
            except Exception as e:
                print(f"Error stopping/removing container {container.name}: {e}")


if __name__ == "__main__":
    image_name = "medidor:latest"  # Nome da imagem a ser utilizada

    # Não é mais necessário construir a imagem aqui, pois isso é feito pelo entrypoint.sh
    try:
        num_replicas = int(os.getenv("NUM_REPLICAS", 1))
        threads, containers = create_replicas(num_replicas, image_name)

        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_and_remove_containers(containers)
