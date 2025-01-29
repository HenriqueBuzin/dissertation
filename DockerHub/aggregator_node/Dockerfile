# Dockerfile

# Usa a imagem base Python com Debian Bullseye
FROM python:3.11.1-bullseye

# Instala pacotes do sistema
RUN apt-get update && apt-get install -y \
    openssh-server supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Configura SSHD
RUN mkdir /var/run/sshd

# Cria usuário aggregator_user
RUN useradd -m aggregator_user \
    && echo "aggregator_user:aggregator_pass" | chpasswd

# Ajusta SSHD
RUN echo "LogLevel VERBOSE" >> /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Cria diretórios para dados e logs
RUN mkdir -p /home/aggregator_user/data/incoming \
    && mkdir -p /home/aggregator_user/data/aggregated \
    && mkdir -p /home/aggregator_user/logs \
    && mkdir -p /remote_path \
    && chown -R aggregator_user:aggregator_user /home/aggregator_user/data \
    && chown -R aggregator_user:aggregator_user /home/aggregator_user/logs \
    && chown aggregator_user:aggregator_user /remote_path \
    && chmod -R 755 /home/aggregator_user/data \
    && chmod -R 755 /home/aggregator_user/logs \
    && chmod 755 /remote_path

# Define o diretório de trabalho /app
WORKDIR /app

# Copia e instala dependências
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia o restante dos arquivos do projeto (app.py, utils/, supervisord.conf, etc.)
COPY . /app/

# Gera chaves SSH
RUN ssh-keygen -A

# Copia o supervisord.conf para /etc/supervisor/conf.d/
RUN mkdir -p /etc/supervisor/conf.d \
    && cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expondo a porta 22 (para SFTP/SSH)
EXPOSE 22

# Comando padrão: inicia o Supervisor, que por sua vez inicia o SSHD e a app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
