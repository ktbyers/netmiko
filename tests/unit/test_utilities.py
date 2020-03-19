#!/usr/bin/env python

import os
from os.path import dirname, join, relpath

from netmiko import utilities
from netmiko._textfsm import _clitable as clitable

RESOURCE_FOLDER = join(dirname(dirname(__file__)), "etc")
RELATIVE_RESOURCE_FOLDER = join(dirname(dirname(relpath(__file__))), "etc")
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
    """
    Search for netmiko_tools config file in the following order:

    NETMIKO_TOOLS_CFG environment variable
    Current directory
    Home directory

    Look for file named: .netmiko.yml or netmiko.yml
    """
    # Search using environment variable (point directly at end file)
    os.environ["NETMIKO_TOOLS_CFG"] = join(RESOURCE_FOLDER, ".netmiko.yml")
    assert utilities.find_cfg_file() == CONFIG_FILENAME

    # Search using environment variable (pointing at directory)
    os.environ["NETMIKO_TOOLS_CFG"] = RESOURCE_FOLDER
    assert utilities.find_cfg_file() == CONFIG_FILENAME

    try:
        cwd = os.getcwd()
        os.chdir(dirname(__file__))

        # Environment var should be preferred over current dir
        assert utilities.find_cfg_file() == CONFIG_FILENAME

        #  Delete env var and verify current dir is returned
        del os.environ["NETMIKO_TOOLS_CFG"]
        assert utilities.find_cfg_file() == "./.netmiko.yml"
    finally:
        # Change directory back to previous state
        os.chdir(cwd)

    # Verify explicit call using full filename
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
    os.environ["NETMIKO_DIR"] = folder
    result = utilities.find_netmiko_dir()
    assert result[0] == folder
    assert result[1].endswith("/tmp")


def test_invalid_netmiko_dir():
    """Try with an invalid netmiko_base_dir"""
    os.environ["NETMIKO_DIR"] = "/"
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
        utilities.write_bytes(456_779)
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


def test_textfsm_w_index():
    """Convert raw CLI output to structured data using TextFSM template"""
    os.environ["NET_TEXTFSM"] = RESOURCE_FOLDER
    raw_output = "Cisco IOS Software, Catalyst 4500 L3 Switch Software"
    result = utilities.get_structured_data(
        raw_output, platform="cisco_ios", command="show version"
    )
    assert result == [{"model": "4500"}]


def test_textfsm_index_relative_path():
    """Test relative path for textfsm ntc directory"""
    os.environ["NET_TEXTFSM"] = RELATIVE_RESOURCE_FOLDER
    raw_output = "Cisco IOS Software, Catalyst 4500 L3 Switch Software"
    result = utilities.get_structured_data(
        raw_output, platform="cisco_ios", command="show version"
    )
    assert result == [{"model": "4500"}]


def test_textfsm_direct_template():
    """Convert raw CLI output to structured data using TextFSM template (no index)."""
    raw_output = "Cisco IOS Software, Catalyst 4500 L3 Switch Software"
    result = utilities.get_structured_data(
        raw_output,
        platform="cisco_ios",
        command="show version",
        template=f"{RESOURCE_FOLDER}/cisco_ios_show_version.template",
    )
    assert result == [{"model": "4500"}]

    # Should also work with no-platform or command
    result = utilities.get_structured_data(
        raw_output, template=f"{RESOURCE_FOLDER}/cisco_ios_show_version.template"
    )
    assert result == [{"model": "4500"}]


def test_textfsm_failed_parsing():
    """Verify raw_output is returned if TextFSM template parsing fails."""
    raw_output = "This is not 'show version' output"
    result = utilities.get_structured_data(
        raw_output,
        platform="cisco_ios",
        command="show version",
        template=f"{RESOURCE_FOLDER}/nothinghere",
    )
    assert result == raw_output


def test_textfsm_missing_template():
    """Verify raw_output is returned if TextFSM template is missing."""
    raw_output = "Cisco IOS Software, Catalyst 4500 L3 Switch Software"
    result = utilities.get_structured_data(
        raw_output,
        platform="cisco_ios",
        command="show version",
        template=f"{RESOURCE_FOLDER}/nothinghere",
    )
    assert result == raw_output


def test_get_structured_data_genie():
    """Convert raw CLI output to structured data using Genie"""

    header_line = (
        "Cisco IOS Software, C3560CX Software (C3560CX-UNIVERSALK9-M), "
        "Version 15.2(4)E7, RELEASE SOFTWARE (fc2)"
    )
    raw_output = """
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2018 by Cisco Systems, Inc.
Compiled Tue 18-Sep-18 13:20 by prod_rel_team

ROM: Bootstrap program is C3560CX boot loader
BOOTLDR: C3560CX Boot Loader (C3560CX-HBOOT-M) Version 15.2(4r)E5, RELEASE SOFTWARE (fc4)

3560CX uptime is 5 weeks, 1 day, 2 hours, 30 minutes
System returned to ROM by power-on
System restarted at 11:45:26 PDT Tue May 7 2019
System image file is "flash:c3560cx-universalk9-mz.152-4.E7.bin"
Last reload reason: power-on



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

License Level: ipservices
License Type: Permanent Right-To-Use
Next reload license Level: ipservices

cisco WS-C3560CX-8PC-S (APM86XXX) processor (revision A0) with 524288K bytes of memory.
Processor board ID FOCXXXXXXXX
Last reset from power-on
5 Virtual Ethernet interfaces
12 Gigabit Ethernet interfaces
The password-recovery mechanism is enabled.

512K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : 12:34:56:78:9A:BC
Motherboard assembly number     : 86-75309-01
Power supply part number        : 867-5309-01
Motherboard serial number       : FOCXXXXXXXX
Power supply serial number      : FOCXXXXXXXX
Model revision number           : A0
Motherboard revision number     : A0
Model number                    : WS-C3560CX-8PC-S
System serial number            : FOCXXXXXXXX
Top Assembly Part Number        : 86-7530-91
Top Assembly Revision Number    : A0
Version ID                      : V01
CLEI Code Number                : CMM1400DRA
Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF
"""
    raw_output = header_line + raw_output
    result = utilities.get_structured_data_genie(
        raw_output, platform="cisco_xe", command="show version"
    )
    assert result["version"]["chassis"] == "WS-C3560CX-8PC-S"
