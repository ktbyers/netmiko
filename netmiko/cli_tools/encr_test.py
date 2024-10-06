import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ENCRYPTION_PREFIX = "__encrypt__"


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

    # Combine salt and encrypted data
    b64_salt = base64.b64encode(salt).decode()
    return f"{ENCRYPTION_PREFIX}{b64_salt}:{base64.b64encode(encrypted).decode()}"


key = input("Enter your encryption key: ").encode()
password = input("Enter the password to encrypt: ")
encryption_type = input("Enter encryption type (fernet or aes128): ")
encrypted = encrypt_value(password, key, encryption_type)
print(f"Encrypted password: {encrypted}")
