# utils/aggregator.py

import re

def identify_type(file_name: str) -> str:
    
    """
    Retorna 'energy' ou 'water', caso encontre no nome do arquivo.
    """
    
    name_lower = file_name.lower()
    if "energy" in name_lower:
        return "energy"
    elif "water" in name_lower:
        return "water"
    return None

def extract_date_from_filename(file_name: str) -> str:
    
    """
    Extrai 8 dígitos (YYYYMMDD) do nome do arquivo.
    """
    
    match = re.search(r"\d{8}", file_name)
    return match.group(0) if match else None
