# utils/general.py

import unicodedata

def normalize_container_name(name):
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
    return name.replace(" ", "_")
