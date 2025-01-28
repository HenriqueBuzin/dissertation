# init_mongo_user.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Configurações MongoDB
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")

# O banco 'admin' será usado para criar o usuário root
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

print("Conectando ao MongoDB para criar usuário...", flush=True)
try:
    client = MongoClient(MONGO_URI)
    db = client["admin"]  # Banco 'admin' para criar usuário com permissão root

    # Criação do usuário root
    db.command("createUser", MONGO_USER, pwd=MONGO_PASS, roles=[{"role": "root", "db": "admin"}])
    print(f"Usuário '{MONGO_USER}' criado com sucesso no banco 'admin'!", flush=True)
except Exception as e:
    print(f"Erro ao criar usuário no MongoDB: {e}", flush=True)
