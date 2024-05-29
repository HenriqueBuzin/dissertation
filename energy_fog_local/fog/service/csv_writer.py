import aiofiles
import csv
from datetime import datetime

async def write_to_csv(data, filename):
    print(f"Iniciando a escrita no arquivo CSV: {filename}")
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        await file.write(','.join(['ID', 'Street', 'Date', 'Consumption_kWh_per_minute']) + '\n')
        for item in data:
            formatted_date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%Y%m%d')
            await file.write(','.join([
                str(item['id']),
                item['street'],
                formatted_date,
                str(item['consumptionKwhPerMinute'])
            ]) + '\n')
            print(f"Escreveu os dados: {item}")
    print(f"Finalizada a escrita no arquivo CSV: {filename}")
    return filename
