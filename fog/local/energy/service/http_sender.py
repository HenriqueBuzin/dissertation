import aiohttp
import aiofiles
import base64
import asyncio
import os

async def send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, url, delay):
    print(f"Iniciando o envio do arquivo: {file_path}")

    remote_path = f"{remote_path}/{file_path}"

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
            
                print(data)
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            print(f"Status da resposta: {response.status}")
                            print(f"Arquivo {file_path} enviado com sucesso.")
                            os.remove(file_path)
                            print(f"Arquivo {file_path} removido.")
                            return
                        else:
                            print(f"Erro ao enviar. Status da resposta: {response.status}. Tentando novamente em {delay} segundos.")
        except Exception as e:
            print(f"Erro ao enviar os dados: {str(e)}")

        await asyncio.sleep(delay)
