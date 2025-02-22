# service/main.py

import os
import asyncio
from service.data_fetcher import fetch_all_consumption

def main():
    async def orchestration_task():
        
        uri = 'http://localhost:8766/graphql'
        protocols_url = 'http://localhost:8000/receive_data'
        interval = 50
        delay = 5
        sftp_host = os.getenv("SFTP_HOST")
        sftp_port = int(os.getenv("SFTP_PORT"))
        sftp_username = os.getenv("SFTP_USER")
        sftp_password = os.getenv("SFTP_PASS")
        remote_path = os.getenv("SFTP_REMOTE_PATH")        
        start_date = '2007-01-01'

        print("Camada de Serviço iniciada.", flush=True)
        try:
            while True:
                await fetch_all_consumption(
                    uri, protocols_url, sftp_host, sftp_port, sftp_username,
                    sftp_password, remote_path, interval, delay, start_date
                )
                await asyncio.sleep(interval)
        finally:
            print("Camada de Serviço encerrando...", flush=True)
            print("Camada de Serviço encerrada.", flush=True)

    asyncio.run(orchestration_task())
