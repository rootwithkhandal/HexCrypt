# core.py — HexCrypt encryption/decryption logic
# pip install cryptography

from cryptography.fernet import Fernet


def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()


def encrypt_text(text: str, key: bytes) -> str:
    """
    Encrypt a plaintext string using the provided Fernet key.

    Args:
        text: The plaintext string to encrypt.
        key:  A valid Fernet key (bytes).

    Returns:
        The encrypted token as a UTF-8 string.

    Raises:
        ValueError: If text or key is empty.
        Exception:  If the key is invalid.
    """
    if not text:
        raise ValueError("Input text cannot be empty.")
    if not key:
        raise ValueError("Encryption key cannot be empty.")

    f = Fernet(key)
    token = f.encrypt(text.encode())
    return token.decode()


def decrypt_text(encrypted_token: str, key: str) -> str:
    """
    Decrypt a Fernet-encrypted token using the provided key.

    Args:
        encrypted_token: The encrypted token string.
        key:             The Fernet key string used during encryption.

    Returns:
        The decrypted plaintext string.

    Raises:
        ValueError: If token or key is empty.
        cryptography.fernet.InvalidToken: If the token or key is invalid.
    """
    if not encrypted_token:
        raise ValueError("Encrypted token cannot be empty.")
    if not key:
        raise ValueError("Decryption key cannot be empty.")

    f = Fernet(key.encode() if isinstance(key, str) else key)
    decrypted = f.decrypt(
        encrypted_token.encode() if isinstance(encrypted_token, str) else encrypted_token
    )
    return decrypted.decode()
