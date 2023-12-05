import docker
import threading

def monitor_container_logs(container, container_number):
    for line in container.logs(stream=True):
        print(f"Contêiner {container_number}: {line.decode('utf-8').strip()}\n")

def create_replicas(num_replicas):
    client = docker.from_env()
    containers = []

    for i in range(1, num_replicas + 1):
        try:
            environment = {"REPLICANUMBER": str(i)}
            container = client.containers.run("medidor", detach=True, environment=environment)
            containers.append(container)
        except Exception as e:
            print(f"Erro ao iniciar o contêiner: {e}")

    threads = []
    for i, container in enumerate(containers, start=1):
        thread = threading.Thread(target=monitor_container_logs, args=(container, i), daemon=True)
        thread.start()
        threads.append(thread)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário, parando contêineres...\n")
        for container in containers:
            try:
                container.stop()
            except Exception as e:
                print(f"Erro ao parar o contêiner: {e}")

    for container in containers:
        try:
            container.wait()
        except Exception as e:
            print(f"Erro ao esperar o contêiner finalizar: {e}")

    print("Todos os contêineres foram parados.")

if __name__ == "__main__":
    num_replicas = int(input("Informe o número de réplicas desejado: "))
    create_replicas(num_replicas)
