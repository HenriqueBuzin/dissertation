import asyncio
import aiohttp
import csv
import json
import os
import aiofiles
import base64

async def write_to_csv(data, filename='consumption.csv'):
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        await file.write(','.join(['ID', 'Street', 'Date', 'Time', 'Consumption_kWh_per_minute']) + '\n')
        for item in data:
            await file.write(','.join([
                str(item['id']),
                item['street'],
                item['date'],
                item['time'],
                str(item['consumptionKwhPerMinute'])
            ]) + '\n')
    return filename

async def send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, url, delay):
    while True:
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                content_base64 = base64.b64encode(content).decode('utf-8')
                data = {
                    "file": content_base64,
                    "type": "ftp",
                    "sftp_host": sftp_host,
                    "sftp_port": sftp_port,
                    "sftp_username": sftp_username,
                    "sftp_password": sftp_password,
                    "remote_path": remote_path
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            print(f"Status da resposta: {response.status}")
                            return
                        else:
                            print(f"Erro ao enviar. Status da resposta: {response.status}. Tentando novamente em {delay} segundos.")
        except Exception as e:
            print(f"Erro ao enviar os dados: {str(e)}")

        await asyncio.sleep(delay)

async def fetch_all_time_and_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, limit, offset):
    while True:
        query = f"""
        {{
            consumptionData(limit: {limit}, offset: {offset}) {{
                id
                street
                date
                time
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

if __name__ == '__main__':
    uri = 'http://processing:8766/graphql'
    protocols_url = 'http://protocols:8000'
    interval = 10
    delay = 5
    sftp_host = '192.168.56.101'
    sftp_port = 22
    sftp_username = 'hpccdemo'
    sftp_password = 'hpccdemo'
    remote_path = '/var/lib/HPCCSystems/mydropzone/consumption.csv'
    limit = 24
    offset = 0

    try:
        asyncio.run(fetch_all_time_and_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, limit, offset))
    except KeyboardInterrupt:
        print("\nColeta de dados encerrando via interrupção pelo usuário...")
    except Exception as e:
        print(f"\nErro durante a execução da coleta de dados: {str(e)}")
    finally:
        print("Coleta de dados encerrada com sucesso.")
