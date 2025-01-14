from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from netmiko.cli_tools import ERROR_PATTERN
from netmiko.cli_tools.helpers import ssh_conn, obtain_devices, update_device_params


BASE_YAML_PATH = Path(__file__).parent / "NETMIKO_YAML"


@pytest.fixture
def mock_connecthandler():
    with patch("netmiko.cli_tools.helpers.ConnectHandler") as mock:
        yield mock


def test_ssh_conn_success(mock_connecthandler):
    mock_net_connect = MagicMock()
    mock_net_connect.send_command.return_value = "Command output"
    mock_net_connect.send_config_set.return_value = "Config output"
    mock_connecthandler.return_value.__enter__.return_value = mock_net_connect

    device_name = "test_device1"
    device_params = {"device_type": "cisco_ios", "host": "192.168.1.1"}

    # Test with cli_command
    result = ssh_conn(device_name, device_params, cli_command="show version")
    assert result == (device_name, "Command output")

    # Test with cfg_command
    result = ssh_conn(
        device_name, device_params, cfg_command=["interface Gi0/1", "description Test"]
    )
    assert result == (device_name, "Config output")


def test_ssh_conn_failure(mock_connecthandler):
    mock_connecthandler.side_effect = Exception("Connection failed")

    device_name = "test_device1"
    device_params = {"device_type": "cisco_ios", "host": "192.168.1.1"}

    result = ssh_conn(device_name, device_params, cli_command="show version")
    assert result == (device_name, ERROR_PATTERN)


@pytest.mark.parametrize(
    "netmiko_yml",
    ["netmiko-cleartext.yml", "netmiko-encr.yml", "netmiko-encr-aes128.yml"],
)
def test_obtain_devices_all(netmiko_yml, monkeypatch, set_encryption_key):
    yml_path = BASE_YAML_PATH / netmiko_yml
    monkeypatch.setenv("NETMIKO_TOOLS_CFG", str(yml_path))
    set_encryption_key()

    result = obtain_devices("all")

    assert len(result) == 7  # Total number of devices
    assert "sf1" in result
    assert "sf2" in result
    assert "den-asa" in result
    assert "den1" in result
    assert "den2" in result
    assert "nyc1" in result
    assert "nyc2" in result

    # Check specific device details
    assert result["sf1"]["device_type"] == "cisco_xe"
    assert result["sf1"]["host"] == "sf-rtr1.bogus.com"
    assert result["sf1"]["username"] == "admin"
    assert result["sf1"]["password"] == "cisco123"

    assert result["den-asa"]["device_type"] == "cisco_asa"
    assert result["den-asa"]["ip"] == "10.1.1.1"
    assert result["den-asa"]["secret"] == "supersecretpass"


BASE_PARAMS = {"device_type": "cisco_ios", "host": "bogus.domain.com"}


@pytest.mark.parametrize(
    "initial_params, update_args, expected_result",
    [
        (
            {**BASE_PARAMS},
            {"username": "admin", "password": "new_pass", "secret": "new_secret"},
            {
                **BASE_PARAMS,
                "username": "admin",
                "password": "new_pass",
                "secret": "new_secret",
            },
        ),
        (
            {**BASE_PARAMS, "username": "old_user"},
            {"password": "new_pass"},
            {**BASE_PARAMS, "username": "old_user", "password": "new_pass"},
        ),
        (
            {**BASE_PARAMS, "username": "user", "password": "pass"},
            {"secret": "new_secret"},
            {
                **BASE_PARAMS,
                "username": "user",
                "password": "pass",
                "secret": "new_secret",
            },
        ),
        (
            {**BASE_PARAMS, "username": "user", "password": "pass", "secret": "secret"},
            {},
            {**BASE_PARAMS, "username": "user", "password": "pass", "secret": "secret"},
        ),
        (
            {**BASE_PARAMS, "username": "existing_user"},
            {"username": "new_user"},
            {
                **BASE_PARAMS,
                "username": "new_user",
            },
        ),
    ],
)
def test_update_device_params(initial_params, update_args, expected_result):
    result = update_device_params(initial_params, **update_args)
    assert result == expected_result, f"Expected {expected_result}, but got {result}"
    assert (
        result is initial_params
    ), "Function should modify the original dictionary, not create a new one"
