# utils/config.py

import os
import json

def load_json(file_path, default=None):

    """
    Carrega um arquivo JSON a partir do caminho especificado.

    Args:
        file_path (str): Caminho completo para o arquivo JSON.
        default (any, optional): Valor padrão a ser retornado caso o arquivo não exista ou ocorra um erro ao carregá-lo.

    Returns:
        dict: Conteúdo do arquivo JSON como dicionário (ou qualquer estrutura definida no arquivo).
        any: O valor padrão, caso o carregamento falhe.
    """

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Erro ao carregar {file_path}")
    return default or {}

def save_json(file_path, data):
    
    """
    Salva um dicionário ou estrutura em um arquivo JSON.

    Args:
        file_path (str): Caminho completo onde o arquivo será salvo.
        data (any): Dados a serem salvos no arquivo, devem ser serializáveis em JSON.

    Returns:
        None
    """

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
