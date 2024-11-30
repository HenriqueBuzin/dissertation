# Dockerfile para o HTTP Data Sender
FROM python:3.9

WORKDIR /app

COPY coap_data_sender.py /app

RUN pip install requests aiocoap

CMD ["python", "coap_data_sender.py"]
