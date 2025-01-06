# service/csv_writer.py

import aiofiles
import csv
from datetime import datetime

async def write_to_csv(data, filename):
    directory = "/app/csv"  # Caminho onde os CSVs serão salvos dentro do container
    full_path = f"{directory}/{filename}"
    print(f"Iniciando a escrita no arquivo CSV: {full_path}", flush=True)
    async with aiofiles.open(full_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        await file.write(','.join(['id', 'street', 'date', 'consumption_kwh_per_day']) + '\n')
        for item in data:
            formatted_date = item['date'].replace('-', '')
            await file.write(','.join([
                str(item['id']),
                item['street'],
                formatted_date,
                str(item['consumptionKwhPerDay'])
            ]) + '\n')
            print(f"Escreveu os dados: {item}", flush=True)
    print(f"Finalizada a escrita no arquivo CSV: {full_path}", flush=True)
    return full_path
