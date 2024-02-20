# Dockerfile para o serviço monitor
FROM python:3.9

RUN pip install docker

COPY ./monitor_replicas.py /monitor_replicas.py

# Instalar Docker CLI (assumindo que você precisa disso para construir imagens, etc.)
RUN apt-get update && apt-get install -y docker.io

# Copiar o script de entrypoint e o código necessário para o diretório /app
COPY entrypoint.sh /app/
COPY . /app/

# Definir o diretório de trabalho
WORKDIR /app

# Tornar o script de entrypoint executável e definí-lo como ENTRYPOINT
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# O comando padrão que será executado pelo entrypoint (pode ser substituído)
CMD ["python", "monitor_replicas.py"]
