# Dockerfile
FROM python:3.13.1
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r processing/requirements.txt
RUN pip install -r protocols/requirements.txt
RUN pip install -r service/requirements.txt
EXPOSE 8765 8766 8000 5683/udp
CMD ["python3", "run.py"]
