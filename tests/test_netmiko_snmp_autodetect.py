#!/usr/bin/env python

from os import path

import pytest

from netmiko.snmp_autodetect import SNMPDetect
from test_utils import parse_yaml


PWD = path.dirname(path.realpath(__file__))


def test_snmp_autodetect(request):
    device_name = request.config.getoption("test_device")
    community = request.config.getoption("snmp_community")

    if not device_name:
        pytest.fail("--test_device is required")
    if not community:
        pytest.fail("--snmp_community is required")

    devices = parse_yaml(path.join(PWD, "etc", "test_devices.yml"))
    device = devices[device_name]
    hostname = device.get("host", device.get("ip"))

    if not hostname:
        pytest.fail(f"No host or ip configured for {device_name}")

    detector = SNMPDetect(
        hostname=hostname,
        snmp_version="v2c",
        community=community,
    )

    assert detector.autodetect() == device["device_type"]


def test_snmpv3_autodetect(request):
    device_name = request.config.getoption("test_device")
    community = request.config.getoption("snmp_community")
    snmp_user = request.config.getoption("snmp_user")

    if not device_name:
        pytest.fail("--test_device is required")
    if not community:
        pytest.fail("--snmp_community is required")
    if not snmp_user:
        pytest.fail("--snmp_user is required")

    devices = parse_yaml(path.join(PWD, "etc", "test_devices.yml"))
    device = devices[device_name]
    hostname = device.get("host", device.get("ip"))

    if not hostname:
        pytest.fail(f"No host or ip configured for {device_name}")

    snmp_key = f"{community}1"
    detector = SNMPDetect(
        hostname=hostname,
        snmp_version="v3",
        user=snmp_user,
        auth_key=snmp_key,
        encrypt_key=snmp_key,
        auth_proto="sha",
        encrypt_proto="aes128",
    )

    assert detector.autodetect() == device["device_type"]
