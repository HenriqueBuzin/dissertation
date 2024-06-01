import aiofiles
import csv

async def write_to_csv(data, filename):
    print(f"Iniciando a escrita no arquivo CSV: {filename}")
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        await file.write(','.join(['id', 'street', 'date', 'time', 'consumption_m3_per_hour']) + '\n')
        for item in data:
            await file.write(','.join([
                str(item['id']),
                item['street'],
                item['date'],
                item['time'],
                str(item['consumptionM3PerHour'])
            ]) + '\n')
            print(f"Escreveu os dados: {item}")
    print(f"Finalizada a escrita no arquivo CSV: {filename}")
    return filename
