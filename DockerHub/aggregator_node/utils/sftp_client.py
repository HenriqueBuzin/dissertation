# utils/sftp_client.py

import paramiko
import logging
import time
import os

logger = logging.getLogger(__name__)

def send_file_sftp(local_file, remote_file, host, port, user, password, retries=3, delay=5):
    """Envia o arquivo 'local_file' para 'remote_file' via SFTP."""
    if not local_file or not os.path.exists(local_file):
        logger.error(f"Arquivo local não encontrado: {local_file}")
        raise FileNotFoundError(f"Arquivo local não encontrado: {local_file}")

    attempt = 0
    while attempt < retries:
        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            logger.info(f"Enviando {local_file} para {host}:{remote_file} via SFTP...")
            sftp.put(local_file, remote_file)

            sftp.close()
            transport.close()
            logger.info("Arquivo enviado com sucesso via SFTP!")
            return True
        except Exception as e:
            attempt += 1
            logger.error(f"Erro ao enviar arquivo via SFTP na tentativa {attempt}: {e}")
            if attempt < retries:
                logger.info(f"Retentando em {delay} segundos...")
                time.sleep(delay)
            else:
                logger.error("Falha ao enviar arquivo via SFTP após múltiplas tentativas.")
                return False
