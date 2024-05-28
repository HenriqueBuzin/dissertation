import asyncio
import aiohttp
from csv_writer import write_to_csv
from http_sender import send_file_and_data_http

async def fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, limit, offset, delay):
    while True:
        query = f"""
        {{
            consumptionData(limit: {limit}, offset: {offset}) {{
                id
                street
                date
                consumptionKwhPerMinute
                type
            }}
        }}
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(uri, json={'query': query}) as response:
                result_json = await response.json(content_type=None)
                data = result_json.get("consumptionData")
                if not data:
                    print("Não há mais dados para coletar. Reiniciando a paginação.")
                    offset = 0
                else:
                    file_path = await write_to_csv(data)
                    await send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, protocols_url, delay)
                    offset += limit

        print(f"Esperando {interval} segundos para a próxima coleta de dados.")
        await asyncio.sleep(interval)
