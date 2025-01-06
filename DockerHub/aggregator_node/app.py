from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os
import csv
import asyncio
from pathlib import Path
from threading import Thread

# Configurações
INCOMING_DIR = "data/incoming"
OUTGOING_FILE = "data/aggregated.csv"
AGGREGATION_INTERVAL = int(os.getenv("AGGREGATION_INTERVAL", 600))

HPCC_SFTP_CONFIG = {
    'host': os.getenv("HPCC_SFTP_HOST"),  # Valor padrão: "hpcc_server"
    'port': int(os.getenv("HPCC_SFTP_PORT")),  # Valor padrão: 22
    'username': os.getenv("HPCC_SFTP_USERNAME"),  # Valor padrão: "hpccdemo"
    'password': os.getenv("HPCC_SFTP_PASSWORD"),  # Valor padrão: "hpccdemo"
    'remote_path': os.getenv("HPCC_SFTP_REMOTE_PATH")  # Valor padrão: "/var/lib/HPCCSystems/mydropzone/aggregated.csv"
}

FTP_SERVER_CONFIG = {
    'host': os.getenv("FTP_SERVER_HOST"),  # Valor padrão: "127.0.0.1"
    'port': int(os.getenv("FTP_SERVER_PORT")),  # Valor padrão: 22
    'username': os.getenv("FTP_SERVER_USERNAME"),  # Valor padrão: "aggregator_user"
    'password': os.getenv("FTP_SERVER_PASSWORD")  # Valor padrão: "aggregator_pass"
}

def start_ftp_server():
    """Inicia um servidor FTP para receber arquivos."""
    os.makedirs(INCOMING_DIR, exist_ok=True)

    try:
        authorizer = DummyAuthorizer()
        authorizer.add_user(
            FTP_SERVER_CONFIG['username'], 
            FTP_SERVER_CONFIG['password'], 
            INCOMING_DIR, 
            perm="elradfmw"
        )

        handler = FTPHandler
        handler.authorizer = authorizer

        print(f"Tentando iniciar o servidor FTP em {FTP_SERVER_CONFIG['host']}:{FTP_SERVER_CONFIG['port']}...", flush=True)
        server = FTPServer((FTP_SERVER_CONFIG['host'], FTP_SERVER_CONFIG['port']), handler)
        print(f"Servidor FTP iniciado em {FTP_SERVER_CONFIG['host']}:{FTP_SERVER_CONFIG['port']}...", flush=True)

        server.serve_forever()
    except Exception as e:
        print(f"Erro ao iniciar o servidor FTP: {e}", flush=True)

def aggregate_files():
    """Agrupa todos os arquivos recebidos em um único arquivo CSV."""
    os.makedirs(Path(OUTGOING_FILE).parent, exist_ok=True)
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

    with open(OUTGOING_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)
    print(f"Arquivo agregado criado: {OUTGOING_FILE}", flush=True)

async def aggregator_main():
    """Loop principal do agregador."""
    while True:
        try:
            aggregate_files()
            await asyncio.sleep(AGGREGATION_INTERVAL)
        except Exception as e:
            print(f"Erro no ciclo do agregador: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando agregador e servidor FTP...", flush=True)
    ftp_thread = Thread(target=start_ftp_server, daemon=True)
    ftp_thread.start()

    try:
        asyncio.run(aggregator_main())
    except KeyboardInterrupt:
        print("\nAgregador e servidor FTP encerrados com sucesso.", flush=True)
