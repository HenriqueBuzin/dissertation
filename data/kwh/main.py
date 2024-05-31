import pandas as pd

# Caminho do arquivo CSV original
input_csv_path = 'household_power_consumption.txt'

# Ler o CSV original com ';' como delimitador e tratar valores não numéricos como NaN
df = pd.read_csv(input_csv_path, sep=';', na_values=['?'], low_memory=False)

# Verificar as primeiras linhas do dataframe para garantir que as colunas foram lidas corretamente
print("Primeiras linhas do dataframe original:")
print(df.head())

# Renomear as colunas 'Date' e 'Time' e calcular 'consumption_kwh_per_hour' a partir de 'Global_active_power'
df['date'] = df['Date']
df['time'] = df['Time']
df['consumption_kwh_per_hour'] = pd.to_numeric(df['Global_active_power'], errors='coerce')

# Selecionar apenas as colunas necessárias
df = df[['date', 'time', 'consumption_kwh_per_hour']]

# Converter a coluna 'date' e 'time' para datetime para facilitar a filtragem e agrupamento
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%d/%m/%Y %H:%M:%S')

# Filtrar os dados para incluir apenas o ano de 2007, de 01/01/2007 a 31/12/2007
start_date = '2007-01-01'
end_date = '2007-12-31'
df_2007 = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
print("Número de registros após filtrar para o ano de 2007:", len(df_2007))

# Verificar se temos dados de todos os meses de 2007
print("Verificação de dados por mês:")
print(df_2007['datetime'].dt.month.value_counts().sort_index())

# Agrupar os dados por hora e calcular a média de 'consumption_kwh_per_hour'
df_2007.set_index('datetime', inplace=True)
df_hourly = df_2007['consumption_kwh_per_hour'].resample('H').mean().reset_index()

# Ordenar os dados agrupados por hora pelo datetime
df_hourly = df_hourly.sort_values(by='datetime')

# Verificar as primeiras linhas do dataframe agrupado
print("Primeiras linhas do dataframe agrupado por hora:")
print(df_hourly.head())

# Separar as colunas 'date' e 'time' novamente
df_hourly['date'] = df_hourly['datetime'].dt.strftime('%Y-%m-%d')
df_hourly['time'] = df_hourly['datetime'].dt.strftime('%H:%M:%S')
df_hourly['consumption_kwh_per_hour'] = df_hourly['consumption_kwh_per_hour'].round(4)
df_hourly = df_hourly[['date', 'time', 'consumption_kwh_per_hour']]

# Verificar as primeiras linhas do dataframe final
print("Primeiras linhas do dataframe final:")
print(df_hourly.head())

# Caminho para salvar o novo CSV com ';' como delimitador
output_csv_path = 'data.csv'

# Salvar o novo CSV com ';' como delimitador e 4 casas decimais
df_hourly.to_csv(output_csv_path, sep=';', index=False, float_format='%.4f')

print(f"Novo CSV salvo em: {output_csv_path}")
