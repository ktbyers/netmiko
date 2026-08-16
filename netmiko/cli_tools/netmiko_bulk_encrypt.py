#!/usr/bin/env python3
# FIX: would be better to have it read the __meta__ field for the encryption type
# if no encryption type is specified.
import argparse
import sys
from pathlib import Path

from netmiko.encryption_handling import encrypt_value, get_encryption_key


def _get_yaml():
    try:
        from ruamel.yaml import YAML
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("ruamel"):
            raise ImportError(
                "netmiko-bulk-encrypt requires the 'bulk-encrypt' extra; "
                "install it with: pip install 'netmiko[bulk-encrypt]'"
            ) from exc
        raise

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def encrypt_netmiko_yml(input_file: str, output_file: str | None, encryption_type: str) -> None:
    yaml = _get_yaml()

    # Read the input YAML file
    input_path = Path(input_file).expanduser()
    with input_path.open("r") as f:
        config = yaml.load(f)

    # Get the encryption key
    key = get_encryption_key()

    # Encrypt password and secret for each device
    for device, params in config.items():
        if isinstance(params, dict):
            if "password" in params:
                encrypted_value = encrypt_value(params["password"], key, encryption_type)
                params["password"] = encrypted_value
            if "secret" in params:
                encrypted_value = encrypt_value(params["secret"], key, encryption_type)
                params["secret"] = encrypted_value

    # Write the updated config to the output file or stdout
    if output_file:
        output_path = Path(output_file)
        with output_path.open("w") as f:
            yaml.dump(config, f)
    else:
        yaml.dump(config, sys.stdout)


def main_ep():
    sys.exit(main())


def main():
    parser = argparse.ArgumentParser(description="Encrypt passwords in .netmiko.yml file")
    parser.add_argument(
        "--input_file",
        default="~/.netmiko.yml",
        help="Input .netmiko.yml file (default: ~/.netmiko.yml)",
    )
    parser.add_argument(
        "--output_file",
        help="Output .netmiko.yml file with encrypted passwords (default: stdout)",
    )
    parser.add_argument(
        "--encryption-type",
        choices=["fernet", "aes128"],
        default="fernet",
        help="Encryption type to use (default: fernet)",
    )

    args = parser.parse_args()

    try:
        encrypt_netmiko_yml(args.input_file, args.output_file, args.encryption_type)
    except ImportError as exc:
        parser.error(str(exc))

    if args.output_file:
        print(
            f"Encrypted .netmiko.yml file has been written to {Path(args.output_file).resolve()}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
