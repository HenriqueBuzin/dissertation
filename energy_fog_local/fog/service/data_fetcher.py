import asyncio
import aiohttp
from datetime import datetime, timedelta
from csv_writer import write_to_csv
from http_sender import send_file_and_data_http

async def fetch_all_consumption(uri, protocols_url, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, interval, limit, offset, delay, start_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')

    while True:
        next_date = current_date + timedelta(days=1)
        print(f"Coletando dados para o dia: {current_date.strftime('%Y-%m-%d')}")

        query = f"""
        {{
            consumptionData(date: "{current_date.strftime('%Y-%m-%d')}", limit: {limit}, offset: {offset}) {{
                id
                street
                date
                consumptionKwhPerMinute
                type
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
                        result_json = await response.json(content_type=None)
                    except Exception as e:
                        print(f"Erro ao decodificar JSON: {str(e)}")
                        result_json = None

                    # print(f"Resposta JSON: {result_json}")

                    # Verificar a estrutura do JSON corretamente
                    if not result_json or not result_json.get('consumptionData'):
                        # print("Resposta JSON vazia ou inválida. Reiniciando a paginação.")
                        offset = 0
                        await asyncio.sleep(interval)
                        continue

                    data = result_json.get('consumptionData')

                    if not data:
                        # print(f"Não há mais dados para coletar para o dia {current_date.strftime('%Y-%m-%d')}. Avançando para o próximo dia.")
                        current_date = next_date
                        offset = 0
                    else:
                        # print(f"Dados retornados: {data}")
                        # Filtrando os dados pela data no lado do cliente
                        filtered_data = [item for item in data if item['date'] == current_date.strftime('%Y-%m-%d') and item.get('consumptionKwhPerMinute') is not None]
                        
                        if filtered_data:
                            print(f"Escrevendo dados no arquivo CSV para o dia {current_date.strftime('%Y-%m-%d')}")
                            file_path = await write_to_csv(filtered_data, f"consumption_energy_{current_date.strftime('%Y-%m-%d')}.csv")
                            print(f"Arquivo CSV criado: {file_path}")
                            await send_file_and_data_http(file_path, sftp_host, sftp_port, sftp_username, sftp_password, remote_path, protocols_url, delay)
                        offset += limit

            except Exception as e:
                print(f"Erro ao fazer a solicitação ou processar a resposta: {str(e)}")

        print(f"Esperando {interval} segundos para a próxima coleta de dados.")
        await asyncio.sleep(interval)
        current_date = next_date
