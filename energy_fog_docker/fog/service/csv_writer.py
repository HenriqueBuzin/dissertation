import aiofiles
import csv
from datetime import datetime

async def write_to_csv(data, filename='consumption.csv'):
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
    return filename
