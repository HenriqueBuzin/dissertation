# Dockerfile

FROM python:3.11.1-bullseye
WORKDIR /app
COPY mqtt_data_sender.py /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
CMD ["python", "mqtt_data_sender.py"]
