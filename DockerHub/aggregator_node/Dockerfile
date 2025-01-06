FROM ubuntu:22.04

# Instala SSH, Python, pip e Supervisor
RUN apt-get update && apt-get install -y \
    openssh-server python3 python3-pip supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cria pasta para o SSHD
RUN mkdir /var/run/sshd

# Cria um usuário "aggregator_user" e define senha
RUN useradd -m aggregator_user
RUN echo "aggregator_user:aggregator_pass" | chpasswd

# Desabilita uso de PAM e permite senha no SSH
RUN sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Cria diretórios para dados e ajusta permissões
RUN mkdir -p /home/aggregator_user/data/incoming
RUN mkdir -p /home/aggregator_user/data/aggregated
RUN chown -R aggregator_user:aggregator_user /home/aggregator_user/data

# Ajusta permissões para os diretórios de dados
RUN chmod -R 777 /home/aggregator_user/data/incoming
RUN chmod -R 777 /home/aggregator_user/data/aggregated

# Instala dependências Python (incluindo paramiko para SFTP)
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copia configuração do Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copia o agregador
WORKDIR /app
COPY app.py /app/

# Expor a porta 22 para SFTP (SSH)
EXPOSE 22

# Inicia o Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
