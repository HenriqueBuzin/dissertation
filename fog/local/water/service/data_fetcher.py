import asyncio
import aiohttp
from datetime import datetime, timedelta
from csv_writer import write_to_csv
from http_sender import send_file_and_data_http

async def fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, delay, start_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')

    while True:
        next_date = current_date + timedelta(days=1)
        print(f"Coletando dados de água para o dia: {current_date.strftime('%Y-%m-%d')}")

        query = f"""
        {{
            waterConsumptionData(date: "{current_date.strftime('%Y-%m-%d')}") {{
                id
                street
                date
                time
                consumptionM3PerHour
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

                    if not result_json or 'waterConsumptionData' not in result_json:
                        print("Resposta JSON vazia ou inválida. Reiniciando a paginação.")
                        await asyncio.sleep(interval)
                        continue

                    data = result_json['waterConsumptionData']

                    if not data:
                        print(f"Não há mais dados para coletar para o dia {current_date.strftime('%Y-%m-%d')}. Avançando para o próximo dia.")
                        current_date = next_date
                    else:
                        print(f"Escrevendo dados no arquivo CSV para o dia {current_date.strftime('%Y-%m-%d')}")
                        file_path = await write_to_csv(data, f"consumption_water_{current_date.strftime('%Y-%m-%d')}.csv")
                        print(f"Arquivo CSV criado: {file_path}")
                        await send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, protocols_url, delay)

            except Exception as e:
                print(f"Erro ao fazer a solicitação ou processar a resposta: {str(e)}")

        print(f"Esperando {interval} segundos para a próxima coleta de dados.")
        await asyncio.sleep(interval)
        current_date = next_date
