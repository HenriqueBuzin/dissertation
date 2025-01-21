import os
import requests
import multiprocessing
import signal
from processing.main import main as processing_main
from protocols.main import main as protocols_main
from service.main import main as service_main

def register_node():
    """Registra o nó no Load Balancer, caso as variáveis de ambiente estejam definidas."""
    lb_url = os.getenv("LOAD_BALANCER_URL")      # ex: http://canasvieiras_load_balancer_1:5000
    node_id = os.getenv("FOG_NODE_NAME")         # ex: canasvieiras_nodo_energy_1
    data_type = os.getenv("NODE_TYPE", "consumption_m3_per_hour")   # ou "energy"; defina uma env ou use valor fixo
    # node_port = os.getenv("HTTP_PORT", "8000")   # porta interna onde o nó escuta requisições
    node__internal_port = os.getenv("NODE_HTTP_PORT", "8000")

    if not lb_url or not node_id:
        print("Variáveis LOAD_BALANCER_URL ou FOG_NODE_NAME não definidas. Pulando registro...")
        return

    # Constrói a URL completa do endpoint de recepção de dados do nó
    node_endpoint = f"http://{node_id}:{node__internal_port}/receive_data"  # Assegure-se de que o Load Balancer pode resolver esse endpoint

    # Constrói os dados para enviar
    data = {
        "node_id": node_id,
        "data_type": data_type,
        "node_endpoint": node_endpoint
    }

    try:
        # Supondo que o LB tenha a rota /register_node
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

        # Registra sinais de interrupção
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
