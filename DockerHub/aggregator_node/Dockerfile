# Dockerfile

# Usa a imagem base Python com Debian Bullseye
FROM python:3.11.1-bullseye

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    openssh-server supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurações do SSHD
RUN mkdir /var/run/sshd

# Cria um usuário "aggregator_user" e define senha
RUN useradd -m aggregator_user \
    && echo "aggregator_user:aggregator_pass" | chpasswd

# Configura SSHD para autenticação por senha e nível de log detalhado
RUN echo "LogLevel VERBOSE" >> /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Cria diretórios para dados e logs, ajusta permissões
RUN mkdir -p /home/aggregator_user/data/incoming \
    && mkdir -p /home/aggregator_user/data/aggregated \
    && mkdir -p /home/aggregator_user/logs \
    && chown -R aggregator_user:aggregator_user /home/aggregator_user/data \
    && chown -R aggregator_user:aggregator_user /home/aggregator_user/logs \
    && chmod -R 755 /home/aggregator_user/data \
    && chmod -R 755 /home/aggregator_user/logs

# Instala dependências Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia os arquivos do projeto
WORKDIR /app
COPY . /app/

# Garante que o arquivo supervisord.conf seja movido para o local correto
RUN mkdir -p /etc/supervisor/conf.d \
    && cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Gera chaves SSH (Necessário para SSHD)
RUN ssh-keygen -A

# Define o usuário padrão como root para o supervisord funcionar corretamente
USER root

# Expor a porta 22 para o SFTP
EXPOSE 22

# Inicia o Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
