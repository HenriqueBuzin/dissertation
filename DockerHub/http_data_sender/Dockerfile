# Dockerfile para o HTTP Data Sender
FROM python:3.9

WORKDIR /app

COPY http_data_sender.py /app

RUN pip install requests

CMD ["python", "http_data_sender.py"]
