# utils/general.py

import unicodedata

def normalize_container_name(name):
    
    """
    Normaliza o nome de um contêiner para uso no Docker, garantindo compatibilidade com o padrão de nomes.

    Args:
        name (str): Nome original que precisa ser normalizado.

    Returns:
        str: Nome normalizado, com caracteres não ASCII removidos e espaços substituídos por underscores.
    """

    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
    return name.replace(" ", "_")
