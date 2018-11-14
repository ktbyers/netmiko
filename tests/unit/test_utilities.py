#!/usr/bin/env python

import os
from os import environ
from os.path import dirname, join, isdir
from uuid import uuid4 as random_uuid

from netmiko import utilities
from netmiko._textfsm import _clitable as clitable

RESOURCE_FOLDER = join(dirname(dirname(__file__)), "etc")
CONFIG_FILENAME = join(RESOURCE_FOLDER, ".netmiko.yml")


def test_load_yaml_file():
    """Read a YAML file successfully"""
    filename = join(RESOURCE_FOLDER, "yaml_test.yml")
    expected = {
        "answer": 42,
        "hello": "world",
        "complex": {"truth": False, "key": "value"},
    }
    assert utilities.load_yaml_file(filename) == expected


def test_invalid_yaml_file():
    """Try to read an invalid YAML file"""
    filename = join(RESOURCE_FOLDER, "this_should_not_exist.yml")
    try:
        utilities.load_yaml_file(filename)
    except SystemExit as exc:
        assert isinstance(exc, SystemExit)
        return
    assert False


def test_find_cfg_file():
    """Try to find a configuration file"""
    assert utilities.find_cfg_file(CONFIG_FILENAME) == CONFIG_FILENAME


def test_load_cfg_file():
    """Try to load a configuration file"""
    expected = {
        "rtr1": {
            "device_type": "cisco_ios",
            "ip": "10.10.10.1",
            "username": "admin",
            "password": "cisco123",
            "secret": "cisco123",
        },
        "rtr2": {
            "device_type": "cisco_ios",
            "ip": "10.10.10.2",
            "username": "admin",
            "password": "cisco123",
            "secret": "cisco123",
        },
        "cisco": ["rtr1", "rtr2"],
    }
    assert utilities.load_devices(CONFIG_FILENAME) == expected


def test_obtain_all_devices():
    """Dynamically create 'all' group."""
    netmiko_tools_load = utilities.load_devices(CONFIG_FILENAME)
    expected = {
        "rtr1": {
            "device_type": "cisco_ios",
            "ip": "10.10.10.1",
            "username": "admin",
            "password": "cisco123",
            "secret": "cisco123",
        },
        "rtr2": {
            "device_type": "cisco_ios",
            "ip": "10.10.10.2",
            "username": "admin",
            "password": "cisco123",
            "secret": "cisco123",
        },
    }
    result = utilities.obtain_all_devices(netmiko_tools_load)
    assert result == expected


def test_find_netmiko_dir():
    """Try to get the netmiko_dir"""
    folder = dirname(__file__)
    environ["NETMIKO_DIR"] = folder
    result = utilities.find_netmiko_dir()
    assert result[0] == folder
    assert result[1].endswith("/tmp")


def test_invalid_netmiko_dir():
    """Try with an invalid netmiko_base_dir"""
    environ["NETMIKO_DIR"] = "/"
    try:
        utilities.find_netmiko_dir()
    except ValueError as exc:
        assert isinstance(exc, ValueError)
        return
    assert False


def test_string_to_bytes():
    """Convert string to bytes"""
    assert utilities.write_bytes("test") == b"test"


def test_bytes_to_bytes():
    """Convert bytes to bytes"""
    result = b"hello world"
    assert utilities.write_bytes(result) == result


def test_invalid_data_to_bytes():
    """Convert an invalid data type to bytes"""
    try:
        utilities.write_bytes(456779)
    except ValueError as exc:
        assert isinstance(exc, ValueError)
        return

    assert False


def test_ensure_resource_dir_exists():
    """Ensure that the resource folder exists"""
    utilities.ensure_dir_exists(RESOURCE_FOLDER)


def test_ensure_file_exists():
    """Ensure that a file makes ensure_dir_exists raise an error"""
    try:
        utilities.ensure_dir_exists(__file__)
    except ValueError as exc:
        assert isinstance(exc, ValueError)
        return
    assert False


def test_clitable_to_dict():
    """Converts TextFSM cli_table object to list of dictionaries"""
    table = clitable.CliTable(template_dir=RESOURCE_FOLDER)
    text_filename = join(RESOURCE_FOLDER, "textfsm.txt")
    template_filename = join(RESOURCE_FOLDER, "cisco_ios_show_version.template")
    with open(text_filename) as data_file:
        text = data_file.read()

    with open(template_filename) as template_file:
        table = table._ParseCmdItem(text, template_file)

    result = utilities.clitable_to_dict(table)
    assert result == [{"model": "4500"}]


def test_get_structured_data():
    """Convert raw CLI output to structured data using TextFSM template"""
    environ["NET_TEXTFSM"] = RESOURCE_FOLDER
    raw_output = "Cisco IOS Software, Catalyst 4500 L3 Switch Software"
    result = utilities.get_structured_data(
        raw_output, platform="cisco_ios", command="show version"
    )
    assert result == [{"model": "4500"}]
