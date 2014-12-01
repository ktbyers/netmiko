#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'router_name'   : 'sf-arista-sw4',
        'router_prompt' : 'sf-arista-sw4>',
        'router_enable' : 'sf-arista-sw4#',
        'interface_ip'  : '10.220.88.31',
        'config_mode'   : '(config)',
    }
    
    SSHClass = netmiko.ssh_dispatcher(arista_veos_sw['device_type'])
    net_connect = SSHClass(**arista_veos_sw)

    # Enter enable mode
    module.router_name = net_connect.router_name
    module.router_prompt_initial = net_connect.router_prompt
    net_connect.enable()
    module.router_prompt = net_connect.router_prompt

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
    assert router_prompt_initial == EXPECTED_RESPONSES['router_prompt']
    assert router_prompt == EXPECTED_RESPONSES['router_enable']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'logging buffered 20010' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
