# run.py

import os
import signal
import requests
import multiprocessing
from service.main import main as service_main
from protocols.main import main as protocols_main
from processing.main import main as processing_main

def register_node():
    lb_url = os.getenv("LOAD_BALANCER_URL")
    node_id = os.getenv("FOG_NODE_NAME")
    data_type = os.getenv("NODE_TYPE", "consumption_m3_per_hour")
    node_internal_port = os.getenv("NODE_HTTP_PORT", "8000")

    if not lb_url or not node_id:
        print("Variáveis LOAD_BALANCER_URL ou FOG_NODE_NAME não definidas. Pulando registro...")
        return

    node_endpoint = f"http://{node_id}:{node_internal_port}/receive_data"

    data = {
        "node_id": node_id,
        "data_type": data_type,
        "node_endpoint": node_endpoint
    }

    try:
        r = requests.post(lb_url + "/register_node", json=data, timeout=5)
        if r.status_code == 200:
            print(f"[INFO] Registro do nó '{node_id}' no LB com sucesso!")
        else:
            print(f"[ERRO] Falha ao registrar no LB: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[ERRO] Exceção ao registrar no LB: {e}")

def start_service(service_main, service_name):
    print(f"{service_name} iniciando...", flush=True)
    try:
        service_main()
    except Exception as e:
        print(f"Erro no {service_name}: {e}", flush=True)
    finally:
        print(f"{service_name} encerrado.", flush=True)

def start_service(service_main, service_name):
    print(f"{service_name} iniciando...", flush=True)
    try:
        service_main()
    except Exception as e:
        print(f"Erro no {service_name}: {e}", flush=True)
    finally:
        print(f"{service_name} encerrado.", flush=True)

def stop_services(processes):
    print("\nSinal de interrupção recebido. Encerrando os serviços...", flush=True)
    for name, process in processes.items():
        if process.is_alive():
            print(f"Encerrando {name}...", flush=True)
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                print(f"{name} não respondeu ao encerramento.", flush=True)
            else:
                print(f"{name} encerrado.", flush=True)
    print("Todos os serviços foram encerrados.", flush=True)

if __name__ == "__main__":
    try:
        register_node()

        processes = {
            "Camada de Processamento": multiprocessing.Process(
                target=start_service, args=(processing_main, "Camada de Processamento")
            ),
            "Camada de Protocolos": multiprocessing.Process(
                target=start_service, args=(protocols_main, "Camada de Protocolos")
            ),
            "Camada de Serviço": multiprocessing.Process(
                target=start_service, args=(service_main, "Camada de Serviço")
            ),
        }

        def signal_handler(sig, frame):
            stop_services(processes)
            raise SystemExit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("Iniciando os serviços...", flush=True)
        for name, process in processes.items():
            process.start()

        for process in processes.values():
            process.join()

    except Exception as e:
        print(f"Erro na execução principal: {e}", flush=True)
    finally:
        print("Execução encerrada.", flush=True)
