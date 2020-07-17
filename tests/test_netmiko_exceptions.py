#!/usr/bin/env python
from os import path
from datetime import datetime
import pytest
from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException
from tests.test_utils import parse_yaml

PWD = path.dirname(path.realpath(__file__))
DEVICE_DICT = parse_yaml(PWD + "/etc/test_devices_exc.yml")


def test_valid_conn():
    """Verify device without modifications works."""
    device = DEVICE_DICT["cisco881_invalid"]
    conn = ConnectHandler(**device)
    assert conn.find_prompt() == "cisco3#"


def test_invalid_port():
    device = DEVICE_DICT["cisco881_invalid"]
    device["port"] = 8022
    with pytest.raises(NetmikoTimeoutException):
        ConnectHandler(**device)


def test_conn_timeout():
    device = DEVICE_DICT["cisco881_invalid"]
    device["conn_timeout"] = 1
    start_time = datetime.now()
    with pytest.raises(NetmikoTimeoutException):
        ConnectHandler(**device)
    end_time = datetime.now()
    time_delta = end_time - start_time
    assert time_delta.total_seconds() < 1.1
