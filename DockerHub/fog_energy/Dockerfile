# Usar Python 3.9 como base
FROM python:3.9

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copiar todos os arquivos do projeto para o contêiner
COPY . /app

# Atualizar o pip e instalar dependências de todos os serviços
RUN pip install --upgrade pip
RUN pip install -r processing/requirements.txt
RUN pip install -r protocols/requirements.txt
RUN pip install -r service/requirements.txt

# Expor as portas necessárias
EXPOSE 8765 8766 8000 5683/udp

# Definir o script principal para rodar todos os serviços
CMD ["python3", "run.py"]
