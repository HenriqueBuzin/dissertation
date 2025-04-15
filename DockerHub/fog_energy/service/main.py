# service/main.py

import os
import asyncio
from service.data_fetcher import fetch_all_consumption

def main():
    async def orchestration_task():
        
        uri = 'http://localhost:8766/graphql'
        protocols_url = 'http://localhost:8000/receive_data'
        delay = 5
        start_date = '2007-01-01'

        interval = int(os.environ.get("NODE_SEND_INTERVAL"))
        aggregator_host = os.environ["AGGREGATOR_HOST"]
        aggregator_port = int(os.environ["AGGREGATOR_PORT"])
        aggregator_user = os.environ["AGGREGATOR_USER"]
        aggregator_pass = os.environ["AGGREGATOR_PASS"]
        remote_path = os.environ["AGGREGATOR_INCOMING_DIR"]

        print("Camada de Serviço iniciada.", flush=True)
        try:
            while True:
                await fetch_all_consumption(
                    uri, protocols_url, aggregator_host, aggregator_port, aggregator_user,
                    aggregator_pass, remote_path, interval, delay, start_date
                )
                await asyncio.sleep(interval)
        finally:
            print("Camada de Serviço encerrando...", flush=True)
            print("Camada de Serviço encerrada.", flush=True)

    asyncio.run(orchestration_task())
