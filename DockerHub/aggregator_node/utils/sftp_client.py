# utils/sftp_client.py

import os
import time
import logging
import paramiko
from pathlib import Path

logger = logging.getLogger(__name__)

HPCC_HOST = "HPCC_HOST"
HPCC_PORT = int(os.environ["HPCC_PORT"])
HPCC_USER = os.environ["HPCC_USER"]
HPCC_PASS = os.environ["HPCC_PASS"]

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
            with paramiko.Transport((HPCC_HOST, HPCC_PORT)) as transport:
                transport.connect(username=HPCC_USER, password=HPCC_PASS)
                with paramiko.SFTPClient.from_transport(transport) as sftp:
                    logger.info(f"SFTP: Enviando {local_file} para {HPCC_HOST}:{remote_file} (tentativa {attempt})")
                    
                    start = time.time()
                    sftp.put(str(local_file), remote_file)
                    end = time.time()

                    elapsed = end - start
                    logger.info(f"[MÉTRICA] Tempo de envio SFTP: {elapsed:.4f} segundos")

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
