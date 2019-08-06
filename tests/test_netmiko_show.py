#!/usr/bin/env python
"""
setup_module: setup variables for later use.

test_disable_paging: disable paging
test_ssh_connect: verify ssh connectivity
test_send_command: send a command
test_send_command_timing: send a command
test_base_prompt: test the base prompt
test_strip_prompt: test removing the prompt
test_strip_command: test stripping extraneous info after sending a command
test_normalize_linefeeds: ensure \n is the only line termination character in output
test_clear_buffer: clear text buffer
test_enable_mode: verify enter enable mode
test_disconnect: cleanly disconnect the SSH session
"""

from __future__ import print_function
from __future__ import unicode_literals
import pytest
import time


def test_disable_paging(net_connect, commands, expected_responses):
    """Verify paging is disabled by looking for string after when paging would normally occur."""
    if net_connect.device_type == "arista_eos":
        # Arista logging buffer gets enormous
        net_connect.send_command("clear logging")
    multiple_line_output = net_connect.send_command(commands["extended_output"])
    assert expected_responses["multiple_line_output"] in multiple_line_output
    if net_connect.device_type == "arista_eos":
        # Arista output is slow and has router-name in output
        time.sleep(5)
        net_connect.clear_buffer()
        net_connect.send_command("clear logging", expect_string="#")


def test_ssh_connect(net_connect, commands, expected_responses):
    """Verify the connection was established successfully."""
    show_version = net_connect.send_command(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_ssh_connect_cm(net_connect_cm, commands, expected_responses):
    """Test the context manager."""
    prompt_str = net_connect_cm
    assert expected_responses["base_prompt"] in prompt_str


def test_send_command_timing(net_connect, commands, expected_responses):
    """Verify a command can be sent down the channel successfully."""
    time.sleep(1)
    net_connect.clear_buffer()
    show_ip = net_connect.send_command_timing(commands["basic"])
    assert expected_responses["interface_ip"] in show_ip


def test_send_command(net_connect, commands, expected_responses):
    """Verify a command can be sent down the channel successfully using send_command method."""
    time.sleep(1)
    net_connect.clear_buffer()
    show_ip_alt = net_connect.send_command(commands["basic"])
    assert expected_responses["interface_ip"] in show_ip_alt


def test_send_command_textfsm(net_connect, commands, expected_responses):
    """Verify a command can be sent down the channel successfully using send_command method."""

    base_platform = net_connect.device_type
    if base_platform.count("_") >= 2:
        # Strip off the _ssh, _telnet, _serial
        base_platform = base_platform.split("_")[:-1]
        base_platform = "_".join(base_platform)

    if base_platform not in [
        "cisco_ios",
        "cisco_xe",
        "cisco_xr",
        "cisco_nxos",
        "arista_eos",
        "cisco_asa",
        "juniper_junos",
        "hp_procurve",
    ]:
        assert pytest.skip("TextFSM/ntc-templates not supported on this platform")
    else:
        time.sleep(1)
        net_connect.clear_buffer()
        fallback_cmd = commands.get("basic")
        command = commands.get("basic_textfsm", fallback_cmd)
        show_ip_alt = net_connect.send_command(command, use_textfsm=True)
        assert isinstance(show_ip_alt, list)


def test_send_command_genie(net_connect, commands, expected_responses):
    """Verify a command can be sent down the channel successfully using send_command method."""

    base_platform = net_connect.device_type
    if base_platform.count("_") >= 2:
        # Strip off the _ssh, _telnet, _serial
        base_platform = base_platform.split("_")[:-1]
        base_platform = "_".join(base_platform)

    if base_platform not in [
        "cisco_ios",
        "cisco_xe",
        "cisco_xr",
        "cisco_nxos",
        "cisco_asa",
    ]:
        assert pytest.skip("TextFSM/ntc-templates not supported on this platform")
    else:
        time.sleep(1)
        net_connect.clear_buffer()
        fallback_cmd = commands.get("basic")
        command = commands.get("basic_textfsm", fallback_cmd)
        show_ip_alt = net_connect.send_command(command, use_genie=True)
        assert isinstance(show_ip_alt, dict)


def test_base_prompt(net_connect, commands, expected_responses):
    """Verify the router prompt is detected correctly."""
    assert net_connect.base_prompt == expected_responses["base_prompt"]


def test_strip_prompt(net_connect, commands, expected_responses):
    """Ensure the router prompt is not in the command output."""

    if expected_responses["base_prompt"] == "":
        return
    show_ip = net_connect.send_command_timing(commands["basic"])
    show_ip_alt = net_connect.send_command(commands["basic"])
    assert expected_responses["base_prompt"] not in show_ip
    assert expected_responses["base_prompt"] not in show_ip_alt


def test_strip_command(net_connect, commands, expected_responses):
    """Ensure that the command that was executed does not show up in the command output."""
    show_ip = net_connect.send_command_timing(commands["basic"])
    show_ip_alt = net_connect.send_command(commands["basic"])
    assert commands["basic"] not in show_ip
    assert commands["basic"] not in show_ip_alt


def test_normalize_linefeeds(net_connect, commands, expected_responses):
    """Ensure no '\r\n' sequences."""
    show_version = net_connect.send_command_timing(commands["version"])
    show_version_alt = net_connect.send_command(commands["version"])
    assert not "\r\n" in show_version
    assert not "\r\n" in show_version_alt


def test_clear_buffer(net_connect, commands, expected_responses):
    """Test that clearing the buffer works."""
    # Manually send a command down the channel so that data needs read.
    net_connect.write_channel(commands["basic"] + "\n")
    time.sleep(4)
    net_connect.clear_buffer()

    # Should not be anything there on the second pass
    clear_buffer_check = net_connect.clear_buffer()
    assert clear_buffer_check is None


def test_enable_mode(net_connect, commands, expected_responses):
    """
    Test entering enable mode

    Catch exception for devices that don't support enable
    """
    try:
        net_connect.enable()
        enable_prompt = net_connect.find_prompt()
        assert enable_prompt == expected_responses["enable_prompt"]
    except AttributeError:
        assert True == True


def test_disconnect(net_connect, commands, expected_responses):
    """Terminate the SSH session."""
    net_connect.disconnect()
