import asyncio
from service.data_fetcher import fetch_all_consumption

def main():
    async def orchestration_task():
        uri = 'http://localhost:8766/graphql'
        protocols_url = 'http://localhost:8000'
        interval = 10
        delay = 5
        sftp_host = 'sftp_server'
        sftp_port = 22
        sftp_username = 'hpccdemo'
        sftp_password = 'hpccdemo'
        remote_path = '/var/lib/HPCCSystems/mydropzone'
        start_date = '2007-01-01'

        print("Camada de Serviço iniciada.")
        try:
            while True:
                await fetch_all_consumption(
                    uri, protocols_url, sftp_host, sftp_port, sftp_username,
                    sftp_password, remote_path, interval, delay, start_date
                )
                await asyncio.sleep(interval)
        finally:
            print("Camada de Serviço encerrando...")
            print("Camada de Serviço encerrada.")

    asyncio.run(orchestration_task())