#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'enable_prompt' : 'xe-test-rtr#',
        'base_prompt'   : 'xe-test-rtr',
        'interface_ip'  : '172.30.0.167',
        'config_mode'   : '(config)',
    }
    
    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'
    
    SSHClass = netmiko.ssh_dispatcher(cisco_xe['device_type'])
    net_connect = SSHClass(**cisco_xe)
    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)

    net_connect.enable()
    module.enable_prompt = net_connect.find_prompt()

    module.config_mode = net_connect.config_mode()

    config_commands = ['logging buffered 20000', 'logging buffered 20010', 'no logging console']
    net_connect.send_config_set(config_commands)

    module.exit_config_mode = net_connect.exit_config_mode()

    module.config_commands_output = net_connect.send_command('show run | inc logging buffer')

    net_connect.disconnect()


def test_enable_mode():
    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'logging buffered 20010' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
