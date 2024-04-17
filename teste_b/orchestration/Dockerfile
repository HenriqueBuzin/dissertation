FROM python:3.12.2-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

COPY wait-for-it.sh ./wait-for-it.sh

RUN chmod +x ./wait-for-it.sh

CMD ["./wait-for-it.sh", "processing:8765", "--", "python", "./main.py"]
