# Dockerfile

FROM python:3.11.1-bullseye
WORKDIR /app
COPY . /app
RUN pip install aiohttp aiocoap
EXPOSE 5000 5683/udp
CMD ["python3", "app.py"]
