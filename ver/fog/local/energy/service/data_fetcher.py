import asyncio
import aiohttp
from datetime import datetime, timedelta
from csv_writer import write_to_csv
from http_sender import send_file_and_data_http

async def fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, delay, start_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')

    while True:
        next_date = current_date + timedelta(days=1)
        print(f"Coletando dados de energia para o dia: {current_date.strftime('%Y-%m-%d')}")

        query = f"""
        {{
            energyConsumptionData(date: "{current_date.strftime('%Y-%m-%d')}") {{
                id
                street
                date
                time
                consumptionKwhPerHour
            }}
        }}
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(uri, json={'query': query}) as response:
                    if response.status != 200:
                        print(f"Erro na solicitação: Status {response.status}")
                        await asyncio.sleep(interval)
                        continue

                    try:
                        result_json = await response.json()
                        print(f"Resposta JSON: {result_json}")
                    except aiohttp.ContentTypeError as e:
                        print(f"Erro ao decodificar JSON (ContentTypeError): {str(e)}")
                        result_json = None
                    except Exception as e:
                        print(f"Erro ao decodificar JSON: {str(e)}")
                        result_json = None

                    if not result_json or 'energyConsumptionData' not in result_json:
                        print("Resposta JSON vazia ou inválida. Reiniciando a paginação.")
                        await asyncio.sleep(interval)
                        continue

                    data = result_json['energyConsumptionData']

                    if not data:
                        print(f"Não há mais dados para coletar para o dia {current_date.strftime('%Y-%m-%d')}. Avançando para o próximo dia.")
                        current_date = next_date
                    else:
                        aggregated_data = {}
                        for item in data:
                            id = item['id']
                            if id not in aggregated_data:
                                aggregated_data[id] = {
                                    'id': id,
                                    'street': item['street'],
                                    'date': item['date'],
                                    'consumptionKwhPerDay': 0.0
                                }
                            try:
                                aggregated_data[id]['consumptionKwhPerDay'] += float(item['consumptionKwhPerHour'])
                            except ValueError:
                                print(f"Valor inválido encontrado em 'consumptionKwhPerHour': {item['consumptionKwhPerHour']}. Definido como 0.")
                                aggregated_data[id]['consumptionKwhPerDay'] += 0.0

                        aggregated_data_list = list(aggregated_data.values())
                        print(f"Escrevendo dados no arquivo CSV para o dia {current_date.strftime('%Y-%m-%d')}")
                        file_path = await write_to_csv(aggregated_data_list, f"consumption_energy_{current_date.strftime('%Y%m%d')}.csv")
                        print(f"Arquivo CSV criado: {file_path}")
                        await send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, protocols_url, delay)

            except Exception as e:
                print(f"Erro ao fazer a solicitação ou processar a resposta: {str(e)}")

        print(f"Esperando {interval} segundos para a próxima coleta de dados.")
        await asyncio.sleep(interval)
        current_date = next_date
