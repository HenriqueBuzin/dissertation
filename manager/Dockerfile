# Dockerfile

FROM python:3.11.1-bullseye

# Define o diretório principal da aplicação
WORKDIR /app

# Copia todo o código do LB
COPY . /app

# Instala as dependências a partir do arquivo
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta necessárias para o protocolo HTTP
EXPOSE 5000

# Define a pasta onde está o app
WORKDIR /app/src

# Comando para iniciar o manager
CMD ["python", "app.py"]
