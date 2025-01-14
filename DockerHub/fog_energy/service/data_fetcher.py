# service/data_fetcher.py

import asyncio
import aiohttp
from datetime import datetime, timedelta
from service.csv_writer import write_to_csv
from service.http_sender import send_file_and_data_http

async def fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, delay, start_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')

    while True:
        # Aguarda o intervalo antes de iniciar a próxima coleta
        print(f"Esperando {interval} segundos antes de coletar dados.", flush=True)
        await asyncio.sleep(interval)

        next_date = current_date + timedelta(days=1)
        print(f"Coletando dados de energia para o dia: {current_date.strftime('%Y-%m-%d')}", flush=True)

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
                        print(f"Erro na solicitação: Status {response.status}", flush=True)
                        continue

                    try:
                        result_json = await response.json()
                        print(f"Resposta JSON: {result_json}")
                    except aiohttp.ContentTypeError as e:
                        print(f"Erro ao decodificar JSON (ContentTypeError): {str(e)}", flush=True)
                        result_json = None
                    except Exception as e:
                        print(f"Erro ao decodificar JSON: {str(e)}", flush=True)
                        result_json = None

                    if not result_json or 'energyConsumptionData' not in result_json:
                        print("Resposta JSON vazia ou inválida. Reiniciando a paginação.", flush=True)
                        continue

                    data = result_json['energyConsumptionData']

                    if not data:
                        print(f"Não há mais dados para coletar para o dia {current_date.strftime('%Y-%m-%d')}. Avançando para o próximo dia.", flush=True)
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
                                print(f"Valor inválido encontrado em 'consumptionKwhPerHour': {item['consumptionKwhPerHour']}. Definido como 0.", flush=True)
                                aggregated_data[id]['consumptionKwhPerDay'] += 0.0

                        aggregated_data_list = list(aggregated_data.values())
                        print(f"Escrevendo dados no arquivo CSV para o dia {current_date.strftime('%Y-%m-%d')}", flush=True)
                        file_path = await write_to_csv(aggregated_data_list, f"consumption_energy_{current_date.strftime('%Y%m%d')}.csv")
                        print(f"Arquivo CSV criado: {file_path}", flush=True)
                        await send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, protocols_url, delay)

            except Exception as e:
                print(f"Erro ao fazer a solicitação ou processar a resposta: {str(e)}", flush=True)

        # Atualiza para o próximo dia após a consulta
        current_date = next_date
