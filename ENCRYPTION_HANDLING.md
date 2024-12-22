# Netmiko Encryption Handling

This document describes the encryption mechanisms available in Netmiko for handling sensitive data in configuration files. These mechanisms are generally intended for use with `~/.netmiko.yml` and Netmiko Tools.

## Overview

Netmiko provides built-in encryption capabilities to secure sensitive data (like passwords) in your Netmiko Tools YAML configuration files. The encryption system is flexible and supports multiple encryption types.

## Configuration

### Basic Setup

Encryption is configured in the `~/.netmiko.yml` file using the `__meta__` field:

```yaml
__meta__:
  encryption: true
  encryption_type: fernet  # or aes128
```

The two supported encryption types are:
- `fernet` (recommended)
- `aes128`

### Encryption Key

The encryption key is read from the environment variable `NETMIKO_TOOLS_KEY`. This should be a secure, randomly-generated key appropriate for the chosen encryption type.

```bash
# Example of setting the encryption key
export NETMIKO_TOOLS_KEY="your-secure-key-here"
```

## Using Encryption

### Encrypted Values in YAML

When encryption is enabled, Netmiko looks for fields that start with `__encrypt__`. For example:

```yaml
arista1:
  device_type: arista_eos
  host: arista1.domain.com
  username: pyclass
  password: >
    __encrypt__ifcs7SWOUER4m1K3ZEZYlw==:Z0FBQUFBQm5CQ9lrdV9BVS0xOWxYelF1Yml
    zV3hBcnF4am1SWjRYNnVSRGdBb1FPVmJ2Q2EzX1RjTWxYMVVMdlBZSXVqYWVqUVNASXNRO
    FBpR1MxRTkxN2J0NWxVeZNKT0E9PQ==
```

### Encryption Functions

#### Encrypting Values

To encrypt a value, use the `encrypt_value` function:

```python
def encrypt_value(value: str, key: bytes, encryption_type: str) -> str:
    """
    Encrypt a value using the specified encryption type.
    
    Args:
        value: The string to encrypt
        key: Encryption key as bytes
        encryption_type: Either 'fernet' or 'aes128'
    
    Returns:
        Encrypted string with '__encrypt__' prefix
    """
```

#### Decrypting Values

To decrypt a value, use the `decrypt_value` function:

```python
def decrypt_value(encrypted_value: str, key: bytes, encryption_type: str) -> str:
    """
    Decrypt a value using the specified encryption type.
    
    Args:
        encrypted_value: The encrypted string (including '__encrypt__' prefix)
        key: Encryption key as bytes
        encryption_type: Either 'fernet' or 'aes128'
    
    Returns:
        Decrypted string
    """
```

#### Getting the Encryption Key

To retrieve the encryption key from the environment:

```python
def get_encryption_key() -> bytes:
    """
    Retrieve the encryption key from NETMIKO_TOOLS_KEY environment variable.
    
    Returns:
        Encryption key as bytes
    """
```

## Example Usage

Here's a complete example of how to use encryption in your code:

```python
from netmiko.encryption_handling import encrypt_value, get_encryption_key
from netmiko.encryption_handling import decrypt_value

# Get the encryption key from environment
key = get_encryption_key()

# Encrypt a password
password = "my_secure_password"
encrypted_password = encrypt_value(password, key, "fernet")

# The encrypted password can now be stored in your YAML file
# It will automatically be decrypted when Netmiko Tools reads the 
# file (assuming you have properly set the '__meta__' fields
```

Alternatively, you can decrypt the value by calling

```python
clear_value = decrypt_value(encrypted_value, key, encryption_type="fernet)
```

Or you can create a simple function to decrypt all of the fields in the YAML
file dynamically (by looking for any fields that start with `__encrypt__`).

Netmiko's 'encryption_handling.py' implements this using the 'decrypt_config'
function, but this function is a specific to Netmiko Tools' .netmiko.yml format 
(i.e. it will need modified if you want to use it in a more generic context).

## Implementation Notes

1. Encryption is processed transparently when Netmiko Tools reads the YAML file
2. Only fields prefixed with `__encrypt__` are processed for decryption
3. The encryption type is determined by the `__meta__` section

## Security Considerations

1. Store the `NETMIKO_TOOLS_KEY` securely and never commit it to version control
2. Fernet encryption is recommended over AES128 as it includes additional security features
3. Encrypted values in YAML files should still be treated as sensitive data
