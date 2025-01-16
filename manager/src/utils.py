# utils.py

import os
import json
import socket
import unicodedata

BASE_PATH = os.getcwd()
JSON_PATH = os.path.join(BASE_PATH, 'jsons')
CONFIG_FILE = os.path.join(JSON_PATH, 'config.json')

def get_available_port(start_port=5000, end_port=6000):
    """Retorna uma porta disponível dentro do intervalo especificado."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("Não há portas disponíveis no intervalo especificado.")

def normalize_container_name(name):
    """Normaliza o nome do contêiner, removendo caracteres especiais e espaços."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.replace(" ", "_")

def load_config():
    """Carrega as configurações do arquivo config.json."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Erro ao decodificar config.json. Retornando configuração padrão.")
                return {"containers": []}
    print("Arquivo config.json não encontrado. Retornando configuração padrão.")
    return {"containers": []}

def save_config(data):
    """Salva as configurações no arquivo config.json."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
