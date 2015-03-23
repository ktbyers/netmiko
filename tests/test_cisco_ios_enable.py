#!/usr/bin/env python
'''
This module runs Cisco IOS enable mode and configuration commands

setup_module: setup variables for later use.

test_enable_mode: verify enter enable mode
test_config_mode: verify enter/exit config mode
test_command_set: verify sending a set of config commands
test_commands_from_file: verify sending a set of config commands from a file
test_exit_enable_mode: verify exit enable mode
test_disconnect: cleanly disconnect the SSH session

'''

from os import path
import time

import pytest

from netmiko import ConnectHandler
from test_utils import parse_yaml


def setup_module(module):

    test_type = 'cisco_ios'

    pwd = path.dirname(path.realpath(__file__))

    responses = parse_yaml(pwd + "/etc/responses.yml")
    module.EXPECTED_RESPONSES = responses[test_type]

    commands = parse_yaml(pwd + "/etc/commands.yml")
    module.commands = commands[test_type]

    test_devices = parse_yaml(pwd + "/etc/test_devices.yml")
    device = test_devices[test_type]
    device['verbose'] = False

    module.net_connect = ConnectHandler(**device)


def test_enable_mode():
    '''
    Test entering enable mode
    '''
    router_prompt = net_connect.find_prompt()
    assert router_prompt == EXPECTED_RESPONSES['router_prompt']
    net_connect.enable()
    enable_prompt = net_connect.find_prompt()
    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    '''
    Test entering/exit config mode
    '''
    config_mode = net_connect.config_mode()
    assert EXPECTED_RESPONSES['config_mode'] in config_mode
    exit_config_mode = net_connect.exit_config_mode()
    assert EXPECTED_RESPONSES['config_mode'] not in exit_config_mode


def test_command_set():
    '''
    Test sending configuration commands
    '''
    config_commands = commands['config']
    net_connect.send_config_set(config_commands[0:1])
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert 'logging buffered 20000' in config_commands_output
    net_connect.send_config_set(config_commands)
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert 'logging buffered 20010' in config_commands_output


def test_commands_from_file():
    '''
    Test sending configuration commands from a file
    '''
    net_connect.send_config_from_file(commands['config_file'])
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert 'logging buffered 8880' in config_commands_output


def test_exit_enable_mode():
    '''
    Test exit enable mode
    '''
    exit_enable_mode = net_connect.exit_enable_mode()
    assert EXPECTED_RESPONSES["router_prompt"] in exit_enable_mode


def test_disconnect():
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()

