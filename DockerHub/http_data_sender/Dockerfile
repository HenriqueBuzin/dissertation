# Dockerfile
FROM python:3.13.1
WORKDIR /app
COPY http_data_sender.py /app
RUN pip install requests
CMD ["python", "http_data_sender.py"]
