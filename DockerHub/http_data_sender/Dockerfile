# Dockerfile

FROM python:3.11.1-bullseye
WORKDIR /app
COPY http_data_sender.py /app
RUN pip install requests
CMD ["python", "http_data_sender.py"]
