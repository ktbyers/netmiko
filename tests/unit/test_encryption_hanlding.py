import pytest
from netmiko.encryption_handling import encrypt_value, decrypt_value, ENCRYPTION_PREFIX


@pytest.mark.parametrize("encryption_type", ["fernet", "aes128"])
def test_encrypt_decrypt(encryption_type):

    original_value = "my_string"

    # Mock encryption key (in real scenarios, this should be securely generated)
    key = b"test_key_1234567890123456"

    # Encrypt the value
    encrypted_value = encrypt_value(original_value, key, encryption_type)

    # Verify the format of the encrypted string
    assert encrypted_value.startswith(ENCRYPTION_PREFIX)

    # Split the encrypted value and verify its parts
    _, rest = encrypted_value.split(ENCRYPTION_PREFIX, 1)
    salt, encrypted_string = rest.split(":", 1)

    # Verify that salt and encrypted_string are not empty
    assert salt
    assert encrypted_string

    # Verify that the salt and encrypted_string are base64 encoded
    import base64

    try:
        base64.b64decode(salt)
        base64.b64decode(encrypted_string)
    except Exception:
        pytest.fail("Salt or encrypted string is not valid base64")

    # Decrypt the value
    decrypted_value = decrypt_value(encrypted_value, key, encryption_type)

    # Verify that the decrypted value matches the original
    assert decrypted_value == original_value
