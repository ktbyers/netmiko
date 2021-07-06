#!/usr/bin/env python
from os import path
from datetime import datetime
import pytest
from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException
from test_utils import parse_yaml

PWD = path.dirname(path.realpath(__file__))
DEVICE_DICT = parse_yaml(PWD + "/etc/test_devices_exc.yml")


def test_valid_conn():
    """Verify device without modifications works."""
    device = DEVICE_DICT["cisco3_invalid"]
    conn = ConnectHandler(**device)
    assert conn.find_prompt() == "cisco3#"


def test_invalid_port():
    device = DEVICE_DICT["cisco3_invalid"]
    device["port"] = 8022
    with pytest.raises(NetmikoTimeoutException):
        ConnectHandler(**device)


def test_conn_timeout():
    device = DEVICE_DICT["cisco3_invalid"]
    device["conn_timeout"] = 5
    device["port"] = 8022
    start_time = datetime.now()
    with pytest.raises(NetmikoTimeoutException):
        ConnectHandler(**device)
    end_time = datetime.now()
    time_delta = end_time - start_time
    assert time_delta.total_seconds() > 5.0
    assert time_delta.total_seconds() < 5.1


def test_dns_fail():
    device = DEVICE_DICT["cisco3_invalid"]
    device["host"] = "invalid.lasthop.io"
    with pytest.raises(NetmikoTimeoutException):
        try:
            ConnectHandler(**device)
        except NetmikoTimeoutException as e:
            assert "DNS failure" in str(e)
            raise


def test_dns_fail_timeout():
    """Should fail very fast."""
    device = DEVICE_DICT["cisco3_invalid"]
    device["host"] = "invalid.lasthop.io"
    start_time = datetime.now()
    with pytest.raises(NetmikoTimeoutException):
        try:
            ConnectHandler(**device)
        except NetmikoTimeoutException as e:
            assert "DNS failure" in str(e)
            raise
    end_time = datetime.now()
    time_delta = end_time - start_time
    assert time_delta.total_seconds() < 0.1


def test_auth_timeout():
    assert True


def test_banner_timeout():
    assert True
