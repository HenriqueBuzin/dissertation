# utils/file_aggregator.py

import os
import csv
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def aggregate_files(incoming_dir, aggregated_dir, outgoing_file):
    """Agrupa todos os arquivos recebidos em um único arquivo CSV."""
    # Valida se os diretórios necessários existem
    for dir_path in [incoming_dir, aggregated_dir]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Diretório criado: {dir_path}")

    # Verifica se há arquivos no diretório de entrada
    files = list(Path(incoming_dir).glob("*.csv"))
    if not files:
        logger.info("Nenhum arquivo disponível para processar no diretório de entrada.")
        return

    all_rows = []
    logger.info("Iniciando agregação de arquivos...")

    for file_path in files:
        try:
            logger.info(f"Processando arquivo recebido: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                all_rows.extend(list(reader))
            os.remove(file_path)
            logger.info(f"Arquivo processado e removido: {file_path.name}")
        except Exception as e:
            logger.error(f"Erro ao processar {file_path.name}: {e}")

    if all_rows:
        try:
            with open(outgoing_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(all_rows)
            logger.info(f"Arquivo agregado criado: {outgoing_file}")
        except Exception as e:
            logger.error(f"Erro ao criar o arquivo agregado: {e}")
    else:
        logger.info("Nenhum conteúdo agregado. Todos os arquivos estavam vazios ou inválidos.")
