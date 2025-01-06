# protocols/utils.py

import os
from dotenv import load_dotenv

def load_env():
    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    dotenv_path = os.path.join(base_dir, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    required_vars = [
        "REDIS_HOST", "REDIS_PORT", "PROTOCOLS_REDIS_DB",
        "MONGO_HOST", "MONGO_PORT", "MONGO_DB", "MONGO_USER",
        "MONGO_PASS", "PROTOCOLS_PERSIST", "PROTOCOLS_MONGO_COLLECTION"
    ]

    env_vars = {}
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            raise ValueError(f"Variável de ambiente {var} não definida")
        env_vars[var] = value

    env_vars["REDIS_PORT"] = int(env_vars["REDIS_PORT"])
    env_vars["PROTOCOLS_REDIS_DB"] = int(env_vars["PROTOCOLS_REDIS_DB"])
    env_vars["MONGO_PORT"] = int(env_vars["MONGO_PORT"])
    env_vars["PROTOCOLS_PERSIST"] = int(env_vars["PROTOCOLS_PERSIST"])

    env_vars["MONGO_URI"] = (
        f"mongodb://{env_vars['MONGO_USER']}:{env_vars['MONGO_PASS']}@"
        f"{env_vars['MONGO_HOST']}:{env_vars['MONGO_PORT']}/"
    )

    return env_vars
