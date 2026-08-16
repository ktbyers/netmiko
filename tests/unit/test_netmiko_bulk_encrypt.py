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
