import json
import os
from hexcrypt import core

VAULT_FILE = "keystore.vault"

def load_vault(password: str) -> dict:
    if not os.path.exists(VAULT_FILE):
        return {}
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        encrypted_data = f.read().strip()
    if not encrypted_data:
        return {}
    json_data = core.decrypt_with_passphrase(encrypted_data, password)
    return json.loads(json_data)

def save_vault(password: str, data: dict):
    json_data = json.dumps(data)
    encrypted_data = core.encrypt_with_passphrase(json_data, password)
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        f.write(encrypted_data)
