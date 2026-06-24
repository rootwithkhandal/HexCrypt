import os
import time
import struct
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

class ExpiredToken(Exception):
    pass

def generate_key() -> str:
    """Generate a new AES-256-GCM key and return as base64."""
    key = AESGCM.generate_key(bit_length=256)
    return base64.urlsafe_b64encode(key).decode('utf-8')

def encrypt_text(input_text: str, key_text: str) -> str:
    """Encrypt the given text using the provided base64 AES-GCM key."""
    key = base64.urlsafe_b64decode(key_text)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, input_text.encode('utf-8'), None)
    
    # Embed 8-byte big-endian timestamp, prefix nonce to ciphertext, and base64 encode
    timestamp = struct.pack(">Q", int(time.time()))
    return base64.urlsafe_b64encode(timestamp + nonce + ciphertext).decode('utf-8')

def decrypt_text(encrypted_text: str, key_text: str, ttl: int = None) -> str:
    """Decrypt the given base64 token using the provided base64 AES-GCM key. Enforces ttl in seconds if provided."""
    key = base64.urlsafe_b64decode(key_text)
    aesgcm = AESGCM(key)
    data = base64.urlsafe_b64decode(encrypted_text)
    if len(data) < 20: # 8 (timestamp) + 12 (nonce)
        raise ValueError("Invalid token size")
        
    timestamp_bytes = data[:8]
    nonce = data[8:20]
    ciphertext = data[20:]
    
    if ttl is not None:
        timestamp = struct.unpack(">Q", timestamp_bytes)[0]
        if int(time.time()) - timestamp > ttl:
            raise ExpiredToken("Token has expired")
            
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')

def encrypt_with_passphrase(input_text: str, passphrase: str) -> str:
    """Encrypt using a key derived from a passphrase via Argon2id."""
    salt = os.urandom(16)
    kdf = Argon2id(salt=salt, length=32, iterations=2, lanes=4, memory_cost=65536)
    key = kdf.derive(passphrase.encode('utf-8'))
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, input_text.encode('utf-8'), None)
    
    # Prefix salt, timestamp, and nonce to ciphertext, then base64 encode
    timestamp = struct.pack(">Q", int(time.time()))
    return base64.urlsafe_b64encode(salt + timestamp + nonce + ciphertext).decode('utf-8')

def decrypt_with_passphrase(encrypted_text: str, passphrase: str, ttl: int = None) -> str:
    """Decrypt a token using a key derived from the embedded salt and a passphrase. Enforces ttl in seconds if provided."""
    data = base64.urlsafe_b64decode(encrypted_text)
    if len(data) < 52:  # 16 (salt) + 8 (timestamp) + 12 (nonce) + 16 (tag)
        raise ValueError("Invalid token size")
        
    salt = data[:16]
    timestamp_bytes = data[16:24]
    nonce = data[24:36]
    ciphertext = data[36:]
    
    if ttl is not None:
        timestamp = struct.unpack(">Q", timestamp_bytes)[0]
        if int(time.time()) - timestamp > ttl:
            raise ExpiredToken("Token has expired")
    
    kdf = Argon2id(salt=salt, length=32, iterations=2, lanes=4, memory_cost=65536)
    key = kdf.derive(passphrase.encode('utf-8'))
    
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')

def encrypt_file(input_path: str, output_path: str, key_text: str):
    """Encrypt a file and write its base64 token to output_path."""
    with open(input_path, 'rb') as f:
        data = f.read()
    
    key = base64.urlsafe_b64decode(key_text)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    
    timestamp = struct.pack(">Q", int(time.time()))
    encrypted_b64 = base64.urlsafe_b64encode(timestamp + nonce + ciphertext).decode('utf-8')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(encrypted_b64)

def decrypt_file(input_path: str, output_path: str, key_text: str, ttl: int = None):
    """Decrypt a file containing a base64 token and write raw bytes to output_path."""
    with open(input_path, 'r', encoding='utf-8') as f:
        encrypted_text = f.read().strip()
        
    key = base64.urlsafe_b64decode(key_text)
    aesgcm = AESGCM(key)
    data = base64.urlsafe_b64decode(encrypted_text)
    if len(data) < 20:
        raise ValueError("Invalid token size")
        
    timestamp_bytes = data[:8]
    nonce = data[8:20]
    ciphertext = data[20:]
    
    if ttl is not None:
        timestamp = struct.unpack(">Q", timestamp_bytes)[0]
        if int(time.time()) - timestamp > ttl:
            raise ExpiredToken("Token has expired")
            
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    with open(output_path, 'wb') as f:
        f.write(plaintext)

def encrypt_file_with_passphrase(input_path: str, output_path: str, passphrase: str):
    """Encrypt a file using a passphrase and write its base64 token to output_path."""
    with open(input_path, 'rb') as f:
        data = f.read()
        
    salt = os.urandom(16)
    kdf = Argon2id(salt=salt, length=32, iterations=2, lanes=4, memory_cost=65536)
    key = kdf.derive(passphrase.encode('utf-8'))
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    
    timestamp = struct.pack(">Q", int(time.time()))
    encrypted_b64 = base64.urlsafe_b64encode(salt + timestamp + nonce + ciphertext).decode('utf-8')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(encrypted_b64)

def decrypt_file_with_passphrase(input_path: str, output_path: str, passphrase: str, ttl: int = None):
    """Decrypt a file containing a base64 token using a passphrase and write raw bytes to output_path."""
    with open(input_path, 'r', encoding='utf-8') as f:
        encrypted_text = f.read().strip()
        
    data = base64.urlsafe_b64decode(encrypted_text)
    if len(data) < 52:
        raise ValueError("Invalid token size")
        
    salt = data[:16]
    timestamp_bytes = data[16:24]
    nonce = data[24:36]
    ciphertext = data[36:]
    
    if ttl is not None:
        timestamp = struct.unpack(">Q", timestamp_bytes)[0]
        if int(time.time()) - timestamp > ttl:
            raise ExpiredToken("Token has expired")
    
    kdf = Argon2id(salt=salt, length=32, iterations=2, lanes=4, memory_cost=65536)
    key = kdf.derive(passphrase.encode('utf-8'))
    
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    with open(output_path, 'wb') as f:
        f.write(plaintext)
