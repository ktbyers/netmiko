#!/usr/bin/env python3
import os
import sys
import argparse
from getpass import getpass

from netmiko.utilities import load_netmiko_yml
from netmiko.encryption_handling import encrypt_value


def main_ep():
    sys.exit(main())


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt data using Netmiko's encryption."
    )
    parser.add_argument("data", help="The data to encrypt", nargs="?")
    parser.add_argument(
        "--key",
        help="The encryption key (if not provided, will use NETMIKO_TOOLS_KEY env variable)",
    )
    parser.add_argument(
        "--type",
        choices=["fernet", "aes128"],
        help="Encryption type (if not provided, will read from .netmiko.yml)",
    )

    args = parser.parse_args()

    if args.data:
        data = args.data
    else:
        data = getpass("Enter the data to encrypt: ")

    # Get encryption key
    if args.key:
        key = args.key.encode()
    else:
        key = os.environ.get("NETMIKO_TOOLS_KEY")
        if not key:
            msg = """Encryption key not provided.
Use --key or set NETMIKO_TOOLS_KEY environment variable."""
            raise ValueError(msg)
        key = key.encode()

    # Get encryption type
    if args.type:
        encryption_type = args.type
    else:
        config_params, my_devices = load_netmiko_yml()
        encryption_type = config_params.get("encryption_type", "fernet")

        if not encryption_type:
            msg = """Encryption type not provided.
Use --type or set 'encryption_type' in .netmiko.yml in the '__meta__' section."""
            raise ValueError(msg)

    # Encrypt the password
    encrypted_data = encrypt_value(data, key, encryption_type)
    print(f"\nEncrypted data: {encrypted_data}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
