import docker
import threading
import time

stop_threads = False  # Flag to signal threads to stop

def monitor_container_logs(container, container_number):
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

def stop_and_remove_containers(containers):
    global stop_threads
    stop_threads = True  # Signal threads to stop
    print("Interrupted by user, stopping and removing containers...\n")
    for container in containers:
        try:
            container.stop()
            container.remove()  # Remove the container after stopping
            print(f"Container removed: {container.name}")
        except Exception as e:
            print(f"Error stopping/removing container: {e}")
    print("All containers have been stopped and removed.")

if __name__ == "__main__":
    try:
        num_replicas = int(input("Enter the desired number of replicas: "))
        threads, containers = create_replicas(num_replicas)

        while True:
            time.sleep(0.1)  # Prevent the main thread from blocking
    except KeyboardInterrupt:
        stop_and_remove_containers(containers)
