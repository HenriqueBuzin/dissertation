# Usa a imagem base Python
FROM python:3.11

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos do agregador
COPY . /app

# Instala as dependências do Python
RUN pip install --no-cache-dir pyftpdlib

# Cria os diretórios necessários
RUN mkdir -p /app/data/incoming

# Exposição de porta para FTP
EXPOSE 2222

# Define o comando de execução
CMD ["python", "app.py"]
