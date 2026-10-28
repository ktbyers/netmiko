from types import SimpleNamespace

import pytest

import netmiko
from netmiko import ConnectHandler  # noqa


def test_placeholder():
    assert True


@pytest.mark.parametrize("minor", [11, 12, 13, 14, 15])
def test_supported_python_version(monkeypatch, minor):
    monkeypatch.setattr(
        target=netmiko,
        name="sys",
        value=SimpleNamespace(version_info=SimpleNamespace(major=3, minor=minor)),
    )
    netmiko.check_python_version()


@pytest.mark.parametrize("major, minor", [(2, 7), (3, 10), (4, 0)])
def test_unsupported_python_version(monkeypatch, major, minor):
    monkeypatch.setattr(
        target=netmiko,
        name="sys",
        value=SimpleNamespace(version_info=SimpleNamespace(major=major, minor=minor)),
    )
    with pytest.raises(expected_exception=ValueError, match="requires Python Version 3\\.11"):
        netmiko.check_python_version()
