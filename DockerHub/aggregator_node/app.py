import os
import csv
import asyncio
from pathlib import Path
import paramiko
import concurrent.futures

# Configurações
INCOMING_DIR = "/home/aggregator_user/data/incoming"
AGGREGATED_DIR = "/home/aggregator_user/data/aggregated"
OUTGOING_FILE = os.path.join(AGGREGATED_DIR, "aggregated.csv")
AGGREGATION_INTERVAL = int(os.getenv("AGGREGATION_INTERVAL", 600))

# Configurações de SFTP para envio
SFTP_HOST = os.getenv("SFTP_HOST", "sftp_server")  # Use o nome do serviço Docker Compose
SFTP_PORT = int(os.getenv("SFTP_PORT", 22))
SFTP_USER = os.getenv("SFTP_USER", "aggregator_user")
SFTP_PASS = os.getenv("SFTP_PASS", "aggregator_pass")
SFTP_REMOTE_PATH = os.getenv("SFTP_REMOTE_PATH", "/home/aggregator_user/data/incoming/consumption_energy_20070101.csv")

def aggregate_files():
    """Agrupa todos os arquivos recebidos em um único arquivo CSV."""
    os.makedirs(Path(AGGREGATED_DIR), exist_ok=True)
    os.makedirs(Path(INCOMING_DIR), exist_ok=True)
    all_rows = []
    print("Iniciando agregação de arquivos...", flush=True)
    
    for file_path in Path(INCOMING_DIR).glob("*.csv"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                all_rows.extend(list(reader))
            os.remove(file_path)
            print(f"Arquivo processado e removido: {file_path}", flush=True)
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}", flush=True)

    if all_rows:
        try:
            with open(OUTGOING_FILE, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(all_rows)
            print(f"Arquivo agregado criado: {OUTGOING_FILE}", flush=True)
        except Exception as e:
            print(f"Erro ao criar o arquivo agregado: {e}", flush=True)
    else:
        print("Nenhum arquivo para agregar.", flush=True)

def send_file_sftp(local_file, remote_file):
    """Envia o arquivo 'local_file' para 'remote_file' via SFTP."""
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        print(f"Enviando {local_file} para {SFTP_HOST}:{remote_file} via SFTP...", flush=True)
        sftp.put(local_file, remote_file)

        sftp.close()
        transport.close()
        print("Arquivo enviado com sucesso via SFTP!", flush=True)
    except Exception as e:
        print(f"Erro ao enviar arquivo via SFTP: {e}", flush=True)

async def send_file_sftp_async(local_file, remote_file):
    """Envia o arquivo via SFTP em um executor para não bloquear o loop assíncrono."""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, send_file_sftp, local_file, remote_file)

async def aggregator_main():
    """Loop principal do agregador."""
    while True:
        try:
            # Agrega os arquivos
            aggregate_files()

            # Envia o arquivo agregado para outro servidor
            if Path(OUTGOING_FILE).exists():
                await send_file_sftp_async(OUTGOING_FILE, SFTP_REMOTE_PATH)
                # Opcional: remover o arquivo após o envio bem-sucedido
                # os.remove(OUTGOING_FILE)
            else:
                print("Nenhum arquivo agregado para enviar.", flush=True)

            # Aguardar o próximo ciclo
            await asyncio.sleep(AGGREGATION_INTERVAL)
        except Exception as e:
            print(f"Erro no ciclo do agregador: {e}", flush=True)
            await asyncio.sleep(AGGREGATION_INTERVAL)  # Garantir que o loop continue

if __name__ == "__main__":
    print("Iniciando agregador (SFTP deve estar rodando em paralelo)...", flush=True)
    try:
        asyncio.run(aggregator_main())
    except KeyboardInterrupt:
        print("\nAgregador encerrado com sucesso.", flush=True)
    except Exception as e:
        print(f"Erro inesperado: {e}", flush=True)
