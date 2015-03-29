#!/usr/bin/env python
"""
This module runs tests against Cisco IOS devices.

setup_module: setup variables for later use.

test_disable_paging: disable paging
test_ssh_connect: verify ssh connectivity
test_send_command: send a command
test_send_command_expect: send a command
test_base_prompt: test the base prompt
test_strip_prompt: test removing the prompt
test_strip_command: test stripping extraneous info after sending a command
test_normalize_linefeeds: ensure \n is the only line termination character in output
test_clear_buffer: clear text buffer
test_enable_mode: verify enter enable mode
test_config_mode: verify enter config mode
test_exit_config_mode: verify exit config mode
test_command_set: verify sending a set of config commands
test_commands_from_file: verify sending a set of config commands from a file
test_exit_enable_mode: verify exit enable mode
test_disconnect: cleanly disconnect the SSH session

"""

from os import path
import time

import pytest

from netmiko import ConnectHandler
from test_utils import parse_yaml


def test_disable_paging(net_connect, commands, expected_responses):
    '''
    Verify paging is disabled by looking for string after when paging would normally occur
    '''

    multiple_line_output = net_connect.send_command(commands["extended_output"])
    assert expected_responses["multiple_line_output"] in multiple_line_output

#
#def test_ssh_connect():
#    '''
#    Verify the connection was established successfully
#    '''
#    show_version = net_connect.send_command(commands["version"])
#    assert EXPECTED_RESPONSES["version_banner"] in show_version
#
#
#def test_send_command():
#    '''
#    Verify a command can be sent down the channel successfully
#    '''
#    show_ip = net_connect.send_command(commands["basic"])
#    assert EXPECTED_RESPONSES['interface_ip'] in show_ip
#
#
#def test_send_command_expect():
#    '''
#    Verify a command can be sent down the channel successfully using _expect method
#    '''
#    show_ip_alt = net_connect.send_command_expect(commands["basic"])
#    assert EXPECTED_RESPONSES['interface_ip'] in show_ip_alt
#
#
#def test_base_prompt():
#    '''
#    Verify the router prompt is detected correctly
#    '''
#    assert net_connect.base_prompt == EXPECTED_RESPONSES['base_prompt']
#
#
#def test_strip_prompt():
#    '''
#    Ensure the router prompt is not in the command output
#    '''
#    show_ip = net_connect.send_command(commands["basic"])
#    show_ip_alt = net_connect.send_command_expect(commands["basic"])
#    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip
#    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip_alt
#
#
#def test_strip_command():
#    '''
#    Ensure that the command that was executed does not show up in the command output
#    '''
#    show_ip = net_connect.send_command(commands["basic"])
#    show_ip_alt = net_connect.send_command_expect(commands["basic"])
#    assert commands['basic'] not in show_ip
#    assert commands['basic'] not in show_ip_alt
#
#
#def test_normalize_linefeeds():
#    '''
#    Ensure no '\r\n' sequences
#    '''
#    show_version = net_connect.send_command(commands["version"])
#    show_version_alt = net_connect.send_command_expect(commands["version"])
#    assert not '\r\n' in show_version
#    assert not '\r\n' in show_version_alt
#
#
#def test_clear_buffer():
#    '''
#    Test that clearing the buffer works
#    '''
#    # Manually send a command down the channel so that data needs read.
#    net_connect.remote_conn.send(commands["basic"] + '\n')
#    time.sleep(2)
#    net_connect.clear_buffer()
#
#    # Should not be anything there on the second pass
#    clear_buffer_check = net_connect.clear_buffer()
#    assert clear_buffer_check is None
#
#
#def test_enable_mode():
#    '''
#    Test entering enable mode
#    '''
#    router_prompt = net_connect.find_prompt()
#    assert router_prompt == EXPECTED_RESPONSES['router_prompt']
#    net_connect.enable()
#    enable_prompt = net_connect.find_prompt()
#    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']
#
#
#def test_config_mode():
#    '''
#    Test enter config mode
#    '''
#    net_connect.config_mode()
#    assert EXPECTED_RESPONSES['config_mode'] in net_connect.find_prompt()
#
#
#def test_exit_config_mode():
#    '''
#    Test exit config mode
#    '''
#    net_connect.exit_config_mode()
#    assert EXPECTED_RESPONSES['config_mode'] not in net_connect.find_prompt()
#
#
#def test_command_set():
#    '''
#    Test sending configuration commands
#    '''
#    config_commands = commands['config']
#    net_connect.send_config_set(config_commands[0:1])
#    config_commands_output = net_connect.send_command('show run | inc logging buffer')
#    assert config_commands[0] in config_commands_output
#    net_connect.send_config_set(config_commands)
#    config_commands_output = net_connect.send_command('show run | inc logging buffer')
#    assert config_commands[-1] in config_commands_output
#
#
#def test_commands_from_file():
#    '''
#    Test sending configuration commands from a file
#    '''
#    net_connect.send_config_from_file(commands['config_file'])
#    config_commands_output = net_connect.send_command('show run | inc logging buffer')
#    assert EXPECTED_RESPONSES["file_check_cmd"] in config_commands_output
#
#
#def test_exit_enable_mode():
#    '''
#    Test exit enable mode
#    '''
#    exit_enable_mode = net_connect.exit_enable_mode()
#    assert EXPECTED_RESPONSES["router_prompt"] in exit_enable_mode
#
#
#def test_disconnect():
#    '''
#    Terminate the SSH session
#    '''
#    net_connect.disconnect()
#
