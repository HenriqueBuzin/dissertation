# init_mongo_user.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")

MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

print("Conectando ao MongoDB para criar usuário...", flush=True)
try:
    client = MongoClient(MONGO_URI)
    db = client["admin"]

    db.command("createUser", MONGO_USER, pwd=MONGO_PASS, roles=[{"role": "root", "db": "admin"}])
    print(f"Usuário '{MONGO_USER}' criado com sucesso no banco 'admin'!", flush=True)
except Exception as e:
    print(f"Erro ao criar usuário no MongoDB: {e}", flush=True)
