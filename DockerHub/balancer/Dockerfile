# Dockerfile
FROM python:3.9
WORKDIR /app
COPY app.py /app
RUN pip install flask
EXPOSE 5000
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]