import aiofiles
import csv

async def write_to_csv(data, filename):
    print(f"Iniciando a escrita no arquivo CSV: {filename}")
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        await file.write(','.join(['id', 'street', 'date', 'consumption_m3_per_day']) + '\n')
        for item in data:
            formatted_date = item['date'].replace('-', '')
            await file.write(','.join([
                str(item['id']),
                item['street'],
                formatted_date,
                str(item['consumptionM3PerDay'])
            ]) + '\n')
            print(f"Escreveu os dados: {item}")
    print(f"Finalizada a escrita no arquivo CSV: {filename}")
    return filename
