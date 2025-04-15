# Dockerfile

# Imagem base com Python 3.11
FROM python:3.11.1-bullseye

# Define diretório de trabalho
WORKDIR /app

# Copia todo o conteúdo do projeto para dentro do container
COPY . /app

# Instala dependências necessárias
RUN pip install --no-cache-dir aiohttp aiocoap requests

# Expõe as portas:
# - 5000: HTTP (API REST)
# - 5683/udp: CoAP (protocolo leve para IoT)
EXPOSE 5000
EXPOSE 5683/udp

# Comando padrão para iniciar o sistema
CMD ["python3", "app.py"]
