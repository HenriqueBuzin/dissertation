# utils/sftp_client.py

import os
import time
import logging
import paramiko
from pathlib import Path

logger = logging.getLogger(__name__)

SFTP_HOST = os.environ["SFTP_HOST"]
SFTP_PORT = int(os.environ["SFTP_PORT"])
SFTP_USER = os.environ["SFTP_USER"]
SFTP_PASS = os.environ["SFTP_PASS"]

def send_file_sftp(local_file: Path, remote_file: str) -> bool:
    """
    Envia local_file -> remote_file via SFTP.
    Faz até 3 tentativas, retornando True (sucesso) ou False (falha).
    """
    if not local_file.exists():
        logger.error(f"SFTP: Arquivo não encontrado: {local_file}")
        return False

    retries = 3
    delay = 5
    for attempt in range(1, retries + 1):
        try:
            with paramiko.Transport((SFTP_HOST, SFTP_PORT)) as transport:
                transport.connect(username=SFTP_USER, password=SFTP_PASS)
                with paramiko.SFTPClient.from_transport(transport) as sftp:
                    logger.info(f"SFTP: Enviando {local_file} para {SFTP_HOST}:{remote_file} (tentativa {attempt})")
                    sftp.put(str(local_file), remote_file)

            logger.info("SFTP: Envio concluído com sucesso.")
            return True
        except Exception as e:
            logger.error(f"SFTP: Erro na tentativa {attempt}: {e}")
            if attempt < retries:
                logger.info(f"SFTP: Retentando em {delay}s...")
                time.sleep(delay)
            else:
                logger.error("SFTP: Falhou após múltiplas tentativas.")
                return False
