# Dockerfile

FROM python:3.11.1-bullseye

RUN apt-get update && apt-get install -y \
    openssh-server supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd

RUN useradd -m aggregator_user \
    && echo "aggregator_user:aggregator_pass" | chpasswd

RUN echo "LogLevel VERBOSE" >> /etc/ssh/sshd_config \
    && sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

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

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

RUN ssh-keygen -A

RUN mkdir -p /etc/supervisor/conf.d \
    && cp /app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 22

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
