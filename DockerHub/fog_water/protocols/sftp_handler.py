import base64
import paramiko
import aiofiles
import os

async def handle_sftp_details_and_send(message):
    try:
        file_content = base64.b64decode(message['file']).decode('utf-8')
        temp_file_path = "temp_file.csv"
        
        async with aiofiles.open(temp_file_path, mode='w', encoding='utf-8') as temp_file:
            await temp_file.write(file_content)
        
        sftp_details = {
            'sftp_host': message['sftp_host'],
            'sftp_port': message['sftp_port'],
            'sftp_username': message['sftp_username'],
            'sftp_password': message['sftp_password'],
            'remote_path': message['remote_path']
        }

        print(sftp_details)
        
        await send_via_sftp(sftp_details, temp_file_path)
    except Exception as e:
        print(f"Erro ao processar os detalhes do SFTP e enviar o arquivo: {e}")

async def send_via_sftp(sftp_details, file_path):
    try:
        print("Iniciando conexão SFTP...")
        print(f"Host: {sftp_details['sftp_host']}, Porta: {sftp_details['sftp_port']}")
        
        transport = paramiko.Transport((sftp_details['sftp_host'], sftp_details['sftp_port']))
        transport.connect(username=sftp_details['sftp_username'], password=sftp_details['sftp_password'])
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"Enviando arquivo {file_path} para {sftp_details['remote_path']}")
        sftp.put(file_path, sftp_details['remote_path'])
        
        print(f"Arquivo {file_path} enviado com sucesso para {sftp_details['remote_path']}.")
        
        sftp.close()
        transport.close()

        try:
            os.remove(file_path)
            print(f"Arquivo temporário {file_path} removido com sucesso.")
        except Exception as e:
            print(f"Erro ao remover o arquivo temporário {file_path}: {e}")

    except paramiko.SSHException as e:
        print(f"Erro SSH ao enviar arquivo via SFTP: {e}")
    except Exception as e:
        print(f"Erro ao enviar arquivo via SFTP: {e}")
