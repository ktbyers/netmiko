import builtins
import sys

import pytest

from netmiko.cli_tools import netmiko_bulk_encrypt


def test_bulk_encrypt_preserves_quotes(tmp_path, monkeypatch):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "output.yml"
    input_file.write_text('router:\n  password: "secret"\n', encoding="utf-8")
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )

    netmiko_bulk_encrypt.encrypt_netmiko_yml(str(input_file), str(output_file), "fernet")

    assert 'password: "encrypted-secret"' in output_file.read_text(encoding="utf-8")


def test_main_success_writes_file_and_returns_zero(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "output.yml"
    input_file.write_text('router:\n  password: "secret"\n', encoding="utf-8")
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "netmiko-bulk-encrypt",
            "--input_file",
            str(input_file),
            "--output_file",
            str(output_file),
        ],
    )

    rc = netmiko_bulk_encrypt.main()

    assert rc == 0
    assert 'password: "encrypted-secret"' in output_file.read_text(encoding="utf-8")
    assert "has been written to" in capsys.readouterr().err


def test_bulk_encrypt_leaves_device_without_credentials_unchanged(tmp_path, monkeypatch):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "output.yml"
    input_file.write_text("switch:\n  device_type: cisco_ios\n  host: 10.0.0.1\n", encoding="utf-8")
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )

    netmiko_bulk_encrypt.encrypt_netmiko_yml(str(input_file), str(output_file), "fernet")

    text = output_file.read_text(encoding="utf-8")
    assert "device_type: cisco_ios" in text
    assert "host: 10.0.0.1" in text
    assert "password" not in text
    assert "secret" not in text


def test_bulk_encrypt_skips_non_dict_entries(tmp_path, monkeypatch):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "output.yml"
    input_file.write_text(
        '__meta__: 1.0\ngroups:\n  - cisco1\ncisco1:\n  password: "secret"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )

    netmiko_bulk_encrypt.encrypt_netmiko_yml(str(input_file), str(output_file), "fernet")

    text = output_file.read_text(encoding="utf-8")
    assert 'password: "encrypted-secret"' in text
    assert "__meta__: 1.0" in text
    assert "- cisco1" in text


def test_bulk_encrypt_encrypts_password_and_secret(tmp_path, monkeypatch):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "output.yml"
    input_file.write_text('router:\n  password: "pw"\n  secret: "en"\n', encoding="utf-8")
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )

    netmiko_bulk_encrypt.encrypt_netmiko_yml(str(input_file), str(output_file), "fernet")

    text = output_file.read_text(encoding="utf-8")
    assert 'password: "encrypted-pw"' in text
    assert 'secret: "encrypted-en"' in text


def test_bulk_encrypt_writes_to_stdout(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.yml"
    input_file.write_text('router:\n  password: "secret"\n', encoding="utf-8")
    monkeypatch.setattr(netmiko_bulk_encrypt, "get_encryption_key", lambda: b"test-key")
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_value",
        lambda value, key, encryption_type: f"encrypted-{value}",
    )

    netmiko_bulk_encrypt.encrypt_netmiko_yml(str(input_file), None, "fernet")

    out = capsys.readouterr().out
    assert 'password: "encrypted-secret"' in out


def test_get_yaml_returns_configured_instance():
    from ruamel.yaml import YAML

    yaml = netmiko_bulk_encrypt._get_yaml()
    assert isinstance(yaml, YAML)
    assert yaml.preserve_quotes is True


def test_bulk_encrypt_missing_optional_dependency(monkeypatch):
    real_import = builtins.__import__

    def missing_ruamel(name, *args, **kwargs):
        if name == "ruamel.yaml":
            raise ModuleNotFoundError("No module named 'ruamel'", name="ruamel")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_ruamel)
    sys.modules.pop("ruamel.yaml", None)

    with pytest.raises(ImportError, match=r"pip install 'netmiko\[bulk-encrypt\]'"):
        netmiko_bulk_encrypt._get_yaml()


def test_bulk_encrypt_cli_missing_optional_dependency(monkeypatch, capsys):
    message = (
        "netmiko-bulk-encrypt requires the 'bulk-encrypt' extra; "
        "install it with: pip install 'netmiko[bulk-encrypt]'"
    )
    monkeypatch.setattr(
        netmiko_bulk_encrypt,
        "encrypt_netmiko_yml",
        lambda *args: (_ for _ in ()).throw(ImportError(message)),
    )
    monkeypatch.setattr(sys, "argv", ["netmiko-bulk-encrypt"])

    with pytest.raises(SystemExit, match="2"):
        netmiko_bulk_encrypt.main()

    assert message in capsys.readouterr().err
