# Dockerfile

# Usa a imagem base Python com Debian Bullseye
FROM python:3.11.1-bullseye

# Instala dependências básicas
RUN apt-get update && apt-get install -y gnupg wget lsb-release redis-server supervisor

# Adiciona o repositório oficial do MongoDB
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg \
    && echo "deb [ signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg ] https://repo.mongodb.org/apt/debian $(lsb_release -cs)/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Instala MongoDB
RUN apt-get update && apt-get install -y mongodb-org

# Cria diretório para MongoDB
RUN mkdir -p /data/db && chown -R mongodb:mongodb /data/db
RUN mkdir -p /var/log/supervisor

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos da aplicação
COPY . /app

# Instala dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r processing/requirements.txt
RUN pip install -r protocols/requirements.txt
RUN pip install -r service/requirements.txt

# Copia script de inicialização do MongoDB
COPY init_mongo_user.py /app/init_mongo_user.py

# Comando para iniciar MongoDB, rodar o script, e habilitar autenticação
RUN mongod --fork --logpath /var/log/mongod.log --dbpath /data/db && \
    python3 /app/init_mongo_user.py && \
    mongod --shutdown

# Exposição de portas
EXPOSE 8765 8766 8000 5683/udp 27017 6379

# Copia a configuração do Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Comando padrão para iniciar tudo com autenticação habilitada
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
