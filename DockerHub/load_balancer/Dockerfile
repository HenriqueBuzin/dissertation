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

# Expõe a porta necessárias para o protocolo CoAP
EXPOSE 5683/udp

# Expõe a porta necessárias para o protocolo MQTT
EXPOSE 1883

# Comando para iniciar o load balancer
CMD ["python3", "app.py"]
