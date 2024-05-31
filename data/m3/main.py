import pandas as pd

# Leitura do arquivo CSV
file_path = 'swm_trialA_1K.csv'
df = pd.read_csv(file_path, delimiter=';')

# Conversão da coluna 'datetime' para o formato datetime
df['datetime'] = pd.to_datetime(df['datetime'], format='%d/%m/%Y %H:%M:%S')

# Filtragem dos dados para o ano de 2026
df_2026 = df[df['datetime'].dt.year == 2016]

# Salvando os dados filtrados em um novo arquivo CSV
output_file_path = 'swm_trialA_2016.csv'
df_2026.to_csv(output_file_path, index=False, sep=';')
