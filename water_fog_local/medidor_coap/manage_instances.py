import os
import sys
import subprocess
from dotenv import load_dotenv

def start_instance(instance_id):
    env = os.environ.copy()
    env['INSTANCE_ID'] = str(instance_id)
    compose_file = 'docker-compose.yml'
    
    try:
        project_name = f"medidor_coap_{instance_id}"
        result = subprocess.run(
            ['docker-compose', '--env-file', '.env', '-f', compose_file, '-p', project_name, 'up', '-d', '--no-deps'],
            env=env,
            capture_output=True, check=True
        )
        if result.returncode != 0:
            print(f"Erro ao iniciar a instância {instance_id}: {result.stderr.decode()}")
        else:
            print(f"Instância {instance_id} iniciada com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao iniciar a instância {instance_id}: {e.stderr.decode()}")

def start_instances(num_instances):
    load_dotenv()

    for i in range(1, num_instances + 1):
        start_instance(i)

def stop_instances():
    compose_file = 'docker-compose.yml'
    try:
        for i in range(1, num_instances + 1):
            project_name = f"medidor_coap_{i}"
            result = subprocess.run(
                ['docker-compose', '-f', compose_file, '-p', project_name, 'down'],
                capture_output=True, check=True
            )
            if result.returncode == 0:
                print(f"Instância {i} parada com sucesso.")
            else:
                print(f"Erro ao parar a instância {i}: {result.stderr.decode()}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao parar as instâncias: {e.stderr.decode()}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python manage_instances.py {start|stop} <número de instâncias>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'start':
        if len(sys.argv) != 3:
            print("Uso: python manage_instances.py start <número de instâncias>")
            sys.exit(1)
        num_instances = int(sys.argv[2])
        start_instances(num_instances)
    elif command == 'stop':
        if len(sys.argv) != 3:
            print("Uso: python manage_instances.py stop <número de instâncias>")
            sys.exit(1)
        num_instances = int(sys.argv[2])
        stop_instances()
    else:
        print("Uso: python manage_instances.py {start|stop} <número de instâncias>")
        sys.exit(1)
