import os
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


ENCRYPTION_PREFIX = "_encrypt_"


def get_encryption_key():
    key = os.environ.get("NETMIKO_TOOLS_KEY")
    if not key:
        raise ValueError(
            "Encryption key not found. Set the 'NETMIKO_TOOLS_KEY' environment variable."
        )
    return key.encode()


def decrypt_value(encrypted_value, key, encryption_type):
    # Remove the encryption prefix
    encrypted_value = encrypted_value.replace(ENCRYPTION_PREFIX, "", 1)

    # Extract salt and ciphertext
    salt, ciphertext = encrypted_value.split(":", 1)
    salt = base64.b64decode(salt)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        return f.decrypt(ciphertext.encode()).decode()
    elif encryption_type == "aes128":
        iv = base64.b64decode(ciphertext[:24])
        ciphertext = base64.b64decode(ciphertext[24:])
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadded = padded[: -padded[-1]]
        return unpadded.decode()
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")


def decrypt_config(config, key, encryption_type):
    for device, params in config.items():
        if isinstance(params, dict):
            for field, value in params.items():
                if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
                    params[field] = decrypt_value(value, key, encryption_type)
    return config


def encrypt_value(value, key, encryption_type):
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        encrypted = f.encrypt(value.encode())
    elif encryption_type == "aes128":
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padded = value.encode() + b"\0" * (16 - len(value) % 16)
        encrypted = iv + encryptor.update(padded) + encryptor.finalize()
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")

    # Combine salt and encrypted data, and add prefix
    b64_salt = base64.b64encode(salt).decode()
    return f"{ENCRYPTION_PREFIX}{b64_salt}:{base64.b64encode(encrypted).decode()}"
