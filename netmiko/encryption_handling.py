import os
import base64
from typing import Dict, Any, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


ENCRYPTION_PREFIX: str = "__encrypt__"


def get_encryption_key() -> bytes:
    key: Union[str, None] = os.environ.get("NETMIKO_TOOLS_KEY")
    if not key:
        raise ValueError(
            "Encryption key not found. Set the 'NETMIKO_TOOLS_KEY' environment variable."
        )
    return key.encode()


def decrypt_value(encrypted_value: str, key: bytes, encryption_type: str) -> str:
    # Remove the encryption prefix
    encrypted_value = encrypted_value.replace(ENCRYPTION_PREFIX, "", 1)

    # Extract salt and ciphertext
    salt_str, ciphertext_str = encrypted_value.split(":", 1)
    salt = base64.b64decode(salt_str)
    ciphertext = base64.b64decode(ciphertext_str)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key: bytes = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        return f.decrypt(ciphertext).decode()
    elif encryption_type == "aes128":
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded: bytes = decryptor.update(ciphertext) + decryptor.finalize()
        unpadded: bytes = padded[: -padded[-1]]
        return unpadded.decode()
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")


def decrypt_config(
    config: Dict[str, Any], key: bytes, encryption_type: str
) -> Dict[str, Any]:
    for device, params in config.items():
        if isinstance(params, dict):
            for field, value in params.items():
                if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
                    len_prefix = len(ENCRYPTION_PREFIX)
                    data: str = value[len_prefix:]
                    params[field] = decrypt_value(data, key, encryption_type)
    return config


def encrypt_value(value: str, key: bytes, encryption_type: str) -> str:
    salt: bytes = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key: bytes = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        fernet_encrypted: bytes = f.encrypt(value.encode())
        encrypted_data = fernet_encrypted
    elif encryption_type == "aes128":
        iv: bytes = os.urandom(16)
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padded: bytes = value.encode() + b"\0" * (16 - len(value) % 16)
        aes_encrypted: bytes = iv + encryptor.update(padded) + encryptor.finalize()
        encrypted_data = aes_encrypted
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")

    # Combine salt and encrypted data, and add prefix
    b64_salt: str = base64.b64encode(salt).decode()
    b64_encrypted: str = base64.b64encode(encrypted_data).decode()
    return f"{ENCRYPTION_PREFIX}{b64_salt}:{b64_encrypted}"
