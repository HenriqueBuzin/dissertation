import pandas as pd
import numpy as np

# Caminho do arquivo de entrada
input_file_path = 'swm_trialA_2016.csv'

# Carregar o arquivo CSV com o delimitador especificado
data = pd.read_csv(input_file_path, delimiter=';')

# Converter a string de datetime para um objeto datetime
data['datetime'] = pd.to_datetime(data['datetime'])

# Arredondar a hora para a mais próxima hora inteira
data['datetime'] = data['datetime'].dt.round('H')

# Função para ajustar o ano, lidando com datas bissextas
def adjust_year(dt, new_year):
    try:
        return dt.replace(year=new_year)
    except ValueError:
        # Lida com o caso de 29 de fevereiro para anos não bissextos
        if dt.month == 2 and dt.day == 29:
            return dt.replace(year=new_year, month=2, day=28)
        raise

# Ajustar o ano para 2007
data['datetime'] = data['datetime'].apply(lambda x: adjust_year(x, 2007))

# Separar em data e hora
data['date'] = data['datetime'].dt.date
data['time'] = data['datetime'].dt.time

# Criar um novo dataframe com os cabeçalhos especificados
result = data[['date', 'time', 'diff']]
result.columns = ['date', 'time', 'consumption_m3_per_hour']

# Ordenar o DataFrame pela coluna 'date' e 'time' para obter a ordem correta
result = result.sort_values(by=['date', 'time'])

# Remover horários duplicados, mantendo a primeira ocorrência
result = result.drop_duplicates(subset=['date', 'time'], keep='first')

# Caminho do arquivo de saída
output_file_path = 'data.csv'

# Salvar o novo dataframe em um arquivo CSV com o delimitador especificado
result.to_csv(output_file_path, sep=';', index=False)

print(f"Arquivo convertido salvo em: {output_file_path}")
