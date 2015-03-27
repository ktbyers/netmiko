#!/usr/bin/env python
"""
This module runs tests against Arista EOS devices.

setup_module: setup variables for later use.

test_disable_paging: disable paging
test_ssh_connect: verify ssh connectivity
test_send_command: send a command
test_send_command_expect: send a command
test_base_prompt: test the base prompt
test_strip_prompt: test removing the prompt
test_strip_command: test stripping extraneous info after sending a command
test_normalize_linefeeds: ensure \n is the only line termination character in output
test_enable_mode: verify enter enable mode
test_config_mode: verify enter/exit config mode
test_command_set: verify sending a set of config commands
test_exit_config_mode: verify exit config mode
test_disconnect: cleanly disconnect the SSH session

"""

from os import path
import time
import re

import pytest

from netmiko import ConnectHandler
from test_utils import parse_yaml


def setup_module(module):
    '''
    Setup variables for tests.
    '''

    test_type = 'arista_eos'

    pwd = path.dirname(path.realpath(__file__))

    responses = parse_yaml(pwd + "/etc/responses.yml")
    module.EXPECTED_RESPONSES = responses[test_type]

    commands = parse_yaml(pwd + "/etc/commands.yml")
    module.commands = commands[test_type]

    test_devices = parse_yaml(pwd + "/etc/test_devices.yml")
    device = test_devices[test_type]
    device['verbose'] = False

    module.net_connect = ConnectHandler(**device)


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    multiple_line_output = net_connect.send_command(commands["extended_output"], delay_factor=4)
    assert EXPECTED_RESPONSES["multiple_line_output"] in multiple_line_output


def test_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    show_version = net_connect.send_command(commands["version"])
    assert EXPECTED_RESPONSES["version_banner"] in show_version


def test_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    show_ip = net_connect.send_command(commands["basic"])
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_send_command_expect():
    '''
    Verify a command can be sent down the channel successfully using _expect method
    '''
    show_ip_alt = net_connect.send_command_expect(commands["basic"])
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip_alt


def test_base_prompt():
    '''
    Verify the router prompt is detected correctly
    '''
    assert net_connect.base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_strip_prompt():
    '''
    Ensure the router prompt is not in the command output
    '''
    show_ip = net_connect.send_command(commands["basic"])
    show_ip_alt = net_connect.send_command_expect(commands["basic"])
    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip
    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip_alt


def test_strip_command():
    '''
    Ensure that the command that was executed does not show up in the 
    command output
    '''
    show_ip = net_connect.send_command(commands["basic"])
    show_ip_alt = net_connect.send_command_expect(commands["basic"])
    assert commands['basic'] not in show_ip
    assert commands['basic'] not in show_ip_alt


def test_normalize_linefeeds():
    '''
    Ensure no '\r\n' sequences
    '''
    show_version = net_connect.send_command(commands["version"])
    show_version_alt = net_connect.send_command_expect(commands["version"])
    assert not '\r\n' in show_version
    assert not '\r\n' in show_version_alt


def test_enable_mode():
    '''
    Verify enter into enable mode
    '''
    assert net_connect.find_prompt() == EXPECTED_RESPONSES['router_prompt']
    net_connect.enable()
    assert net_connect.find_prompt() == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    '''
    Verify enter into configuration mode
    '''
    net_connect.config_mode()
    assert EXPECTED_RESPONSES['config_mode'] in net_connect.find_prompt()


def test_command_set():
    '''
    Test sending configuration commands
    '''
    config_commands = commands['config']
    net_connect.send_config_set(config_commands[0:1])
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert config_commands[0] in config_commands_output
    net_connect.send_config_set(config_commands)
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert config_commands[-1] in config_commands_output


def test_exit_config_mode():
    '''
    Verify exit configuration mode
    '''
    net_connect.exit_config_mode()
    assert not EXPECTED_RESPONSES['config_mode'] in net_connect.find_prompt()


def test_disconnect():
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()
