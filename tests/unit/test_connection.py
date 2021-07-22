#!/usr/bin/env python
import pytest
import logging
from netmiko import ConnectHandler, ConnLogOnly, ConnUnify
from netmiko import NetmikoAuthenticationException
from netmiko import NetmikoTimeoutException
from netmiko import ConnectionException


# Fictional devices that will fail
DEVICE1 = {
    "host": "localhost",
    "device_type": "linux",
    "username": "bogus",
    "password": "bogus",
}

DEVICE2 = {
    "host": "localhost",
    "device_type": "linux",
    "username": "bogus",
    "password": "bogus",
    "port": 8022,
}


def test_connecthandler():
    with pytest.raises(NetmikoAuthenticationException):
        net_connect = ConnectHandler(**DEVICE1)
    with pytest.raises(NetmikoTimeoutException):
        net_connect = ConnectHandler(**DEVICE2)  # noqa


def test_connlogonly(caplog):
    log_level = logging.INFO
    log_file = "my_output.log"

    net_connect = ConnLogOnly(log_file=log_file, log_level=log_level, **DEVICE1)
    assert net_connect is None
    net_connect = ConnLogOnly(log_file=log_file, log_level=log_level, **DEVICE2)
    assert net_connect is None

    assert "ERROR" in caplog.text
    assert caplog.text.count("ERROR") == 2
    assert "Authentication failure" in caplog.text
    assert "was unable to reach the provided host and port" in caplog.text


def test_connunify():
    with pytest.raises(ConnectionException):
        net_connect = ConnUnify(**DEVICE1)
    with pytest.raises(ConnectionException):
        net_connect = ConnUnify(**DEVICE2)  # noqa
