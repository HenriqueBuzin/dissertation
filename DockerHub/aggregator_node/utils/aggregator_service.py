# utils/aggregator_service.py

import os
import csv
import logging
import asyncio
from pathlib import Path
from collections import defaultdict
from .sftp_client import send_file_sftp
from .aggregator import identify_type, extract_date_from_filename

logger = logging.getLogger(__name__)

INCOMING_DIR = os.environ["INCOMING_DIR"]
AGGREGATED_DIR = os.environ["AGGREGATED_DIR"]
AGGREGATION_INTERVAL = int(os.environ["AGGREGATION_INTERVAL"])
REMOTE_PATH = os.environ["REMOTE_PATH"]

async def aggregator_task():

    """
    Processa arquivos de consumo e gera um consolidado diário separado por tipo:
    - `aggregated_energy_YYYYMMDD.csv` → Consumo de energia (`consumption_kwh_per_day`).
    - `aggregated_water_YYYYMMDD.csv` → Consumo de água (`consumption_m3_per_day`).
    
    Mantém o mesmo cabeçalho dos arquivos recebidos e soma valores por ID.
    """

    Path(INCOMING_DIR).mkdir(parents=True, exist_ok=True)
    Path(AGGREGATED_DIR).mkdir(parents=True, exist_ok=True)

    while True:
        try:
            files = list(Path(INCOMING_DIR).glob("*.csv"))
            if not files:
                logger.info("[AGGREGATOR_TASK] Nenhum arquivo disponível.")
                await asyncio.sleep(AGGREGATION_INTERVAL)
                continue

            # Dicionário para armazenar dados agregados
            data_by_type_and_date = {
                "energy": defaultdict(lambda: defaultdict(float)),  # {YYYYMMDD: {id: consumo_somado}}
                "water": defaultdict(lambda: defaultdict(float))
            }

            # Mapeamento de cabeçalhos para manter o formato original
            headers_by_type = {"energy": None, "water": None}

            for file_path in files:
                fname = file_path.name

                dt_type = identify_type(fname)
                if not dt_type:
                    logger.warning(f"Ignorando {fname}: tipo desconhecido.")
                    continue

                dt_date = extract_date_from_filename(fname)
                if not dt_date or len(dt_date) != 8:
                    logger.warning(f"Ignorando {fname}: data inválida.")
                    continue

                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)

                        # Ajuste do cabeçalho para reconhecer os nomes reais
                        field_mapping = {
                            "energy": ["consumptionKwhPerDay", "consumption_kwh_per_day"],
                            "water": ["consumptionM3PerDay", "consumption_m3_per_day"]
                        }

                        headers_by_type[dt_type] = reader.fieldnames  # Guarda os cabeçalhos originais
                        for row in reader:
                            row_id = row.get("id")
                            if not row_id:
                                continue

                            # Ajusta o nome do campo de consumo dependendo do tipo
                            consumption_value = 0.0
                            for possible_field in field_mapping[dt_type]:
                                if possible_field in row:
                                    consumption_value = float(row.get(possible_field, 0) or 0)
                                    break  # Para no primeiro que encontrar

                            # Soma o consumo por ID
                            data_by_type_and_date[dt_type][dt_date][row_id] += consumption_value

                    file_path.unlink()
                    logger.info(f"Processado e removido: {fname}")

                except Exception as e:
                    logger.error(f"Erro ao processar {fname}: {e}")

            # Criar os arquivos agregados
            aggregated_files = []
            for dt_type, dates_map in data_by_type_and_date.items():
                for dt_date, row_map in dates_map.items():
                    out_name = f"aggregated_{dt_type}_{dt_date}.csv"
                    out_path = Path(AGGREGATED_DIR) / out_name

                    # Mantém os cabeçalhos originais
                    fieldnames = headers_by_type[dt_type] if headers_by_type[dt_type] else ["id", "street", "date", "consumption"]

                    with out_path.open("w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for row_id, consumption in row_map.items():
                            writer.writerow({
                                "id": row_id,
                                "street": "",  # O campo 'street' pode estar ausente, então mantemos vazio
                                "date": dt_date,
                                "consumption_kwh_per_day" if dt_type == "energy" else "consumption_m3_per_day": consumption
                            })

                    logger.info(f"Criado {out_path}")
                    aggregated_files.append(out_path)

            # Enviar arquivos por SFTP
            for agg_file in aggregated_files:
                remote_file = os.path.join(REMOTE_PATH, agg_file.name)
                logger.info(f"Enviando {agg_file} -> {remote_file}")

                success = send_file_sftp(agg_file, remote_file)
                if success:
                    agg_file.unlink()
                    logger.info(f"{agg_file} enviado e removido.")
                else:
                    logger.error(f"Falha no envio de {agg_file}, mantendo local.")

        except Exception as e:
            logger.error(f"Erro no loop do agregador: {e}")

        await asyncio.sleep(AGGREGATION_INTERVAL)
