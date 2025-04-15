# app.py

from utils import aggregator_task
import asyncio
import logging
import socket
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

AGGREGATOR_INCOMING_DIR = os.environ["AGGREGATOR_INCOMING_DIR"]
AGGREGATOR_AGGREGATED_DIR = os.environ["AGGREGATOR_AGGREGATED_DIR"]
AGGREGATOR_AGGREGATION_INTERVAL = int(os.environ["AGGREGATOR_AGGREGATION_INTERVAL"])

HPCC_HOST = "HPCC_HOST"
HPCC_PORT = int(os.environ["HPCC_PORT"])
HPCC_USER = os.environ["HPCC_USER"]
HPCC_PASS = os.environ["HPCC_PASS"]
HPCC_REMOTE_PATH = os.environ["HPCC_REMOTE_PATH"]

try:
    resolved_ip = socket.gethostbyname(HPCC_HOST)
except Exception as e:
    resolved_ip = f"Erro ao resolver: {e}"

logger.info(f"[CONFIG] AGGREGATOR_INCOMING_DIR={AGGREGATOR_INCOMING_DIR}")
logger.info(f"[CONFIG] AGGREGATOR_AGGREGATED_DIR={AGGREGATOR_AGGREGATED_DIR}")
logger.info(f"[CONFIG] AGGREGATOR_AGGREGATION_INTERVAL={AGGREGATOR_AGGREGATION_INTERVAL}")

logger.info(f"[CONFIG] HPCC_HOST={HPCC_HOST} → {resolved_ip}, HPCC_PORT={HPCC_PORT}, HPCC_USER={HPCC_USER}")
logger.debug(f"[CONFIG] HPCC_PASS={HPCC_PASS}, HPCC_REMOTE_PATH={HPCC_REMOTE_PATH}")

async def main():
    logger.info("Iniciando agregador.")
    await aggregator_task()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Aplicação encerrada via Ctrl+C.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
