import multiprocessing
import signal
import time
from processing.main import main as processing_main
from protocols.main import main as protocols_main
from service.main import main as orchestration_main

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
        processes = {
            "Camada de Processamento": multiprocessing.Process(
                target=start_service, args=(processing_main, "Camada de Processamento")
            ),
            "Camada de Protocolos": multiprocessing.Process(
                target=start_service, args=(protocols_main, "Camada de Protocolos")
            ),
            "Camada de Serviço": multiprocessing.Process(
                target=start_service, args=(orchestration_main, "Camada de Serviço")
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
