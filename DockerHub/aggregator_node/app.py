# app.py

import os
import asyncio
import logging
from dotenv import load_dotenv
from utils import aggregate_files, send_file_sftp
import datetime

# Carrega variáveis de ambiente do .env, caso ainda não estejam definidas
load_dotenv()

# Lista de variáveis obrigatórias
REQUIRED_ENV_VARS = [
    "AGGREGATION_INTERVAL", "INCOMING_DIR", "AGGREGATED_DIR", "OUTGOING_FILE",
    "SFTP_HOST", "SFTP_PORT", "SFTP_USER", "SFTP_PASS"
]

# Configuração do Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Valida e carrega as variáveis de ambiente
logger.info("Validando e carregando variáveis de ambiente...")
config = {}
for var in REQUIRED_ENV_VARS:
    value = os.getenv(var)
    if not value:
        logger.error(f"Variável de ambiente obrigatória não definida: {var}")
        raise ValueError(f"Variável de ambiente obrigatória não definida: {var}")
    config[var] = value
    logger.info(f"{var} = {value}")

# Converte AGGREGATION_INTERVAL e SFTP_PORT para inteiros
config["AGGREGATION_INTERVAL"] = int(config["AGGREGATION_INTERVAL"])
config["SFTP_PORT"] = int(config["SFTP_PORT"])

# Valida se os diretórios existem
for dir_path in [config["INCOMING_DIR"], config["AGGREGATED_DIR"]]:
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Diretório criado: {dir_path}")

def generate_remote_path(base_path, prefix="aggregated"):
    """Gera um nome dinâmico para o arquivo remoto."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}_{timestamp}.csv"
    return os.path.join(base_path, filename)

async def aggregator_main(config):
    """Loop principal do agregador."""
    while True:
        try:
            aggregate_files(
                incoming_dir=config["INCOMING_DIR"],
                aggregated_dir=config["AGGREGATED_DIR"],
                outgoing_file=config["OUTGOING_FILE"]
            )

            if os.path.exists(config["OUTGOING_FILE"]):
                remote_file_path = generate_remote_path(config["INCOMING_DIR"])
                logger.info(f"Preparando para enviar arquivo agregado: {config['OUTGOING_FILE']} para {remote_file_path}")
                success = send_file_sftp(
                    local_file=config["OUTGOING_FILE"],
                    remote_file=remote_file_path,
                    host=config["SFTP_HOST"],
                    port=config["SFTP_PORT"],
                    user=config["SFTP_USER"],
                    password=config["SFTP_PASS"]
                )
                if success:
                    os.remove(config["OUTGOING_FILE"])
                    logger.info(f"Arquivo agregado removido após envio: {config['OUTGOING_FILE']}")
                else:
                    logger.error("Falha ao enviar o arquivo agregado via SFTP.")
            else:
                logger.info("Nenhum arquivo agregado disponível para envio.")

            await asyncio.sleep(config["AGGREGATION_INTERVAL"])
        except Exception as e:
            logger.error(f"Erro no ciclo do agregador: {e}")
            await asyncio.sleep(config["AGGREGATION_INTERVAL"])

if __name__ == "__main__":
    logger.info("Iniciando agregador (SFTP deve estar rodando em paralelo)...")
    try:
        asyncio.run(aggregator_main(config))
    except KeyboardInterrupt:
        logger.info("Agregador encerrado com sucesso.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
