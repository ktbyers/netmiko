#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'sf-arista-sw4',
        'interface_ip'  : '10.220.88.31',
        'config_mode'   : '(config)',
    }
    
    SSHClass = netmiko.ssh_dispatcher(arista_veos_sw['device_type'])
    net_connect = SSHClass(**arista_veos_sw)

    # Enter enable mode
    module.base_prompt_initial = net_connect.base_prompt
    net_connect.enable()
    module.base_prompt = net_connect.base_prompt

    # Send a set of config commands
    module.config_mode = net_connect.config_mode()
    config_commands = ['logging buffered 20000', 'logging buffered 20010', 'no logging console']
    net_connect.send_config_set(config_commands)

    # Exit config mode
    module.exit_config_mode = net_connect.exit_config_mode()

    # Verify config changes 
    module.config_commands_output = net_connect.send_command('show run | inc logging buffer')

    net_connect.disconnect()


def test_enable_mode():
    assert base_prompt_initial == EXPECTED_RESPONSES['base_prompt']
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'logging buffered 20010' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
