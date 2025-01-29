# app.py

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from utils import aggregator_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

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
