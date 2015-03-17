#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt'      : 'pynet-rtr1',
        'user_exec_prompt' : 'pynet-rtr1>',
        'enable_prompt'    : 'pynet-rtr1#',
        'interface_ip'     : '10.220.88.20',
        'config_mode'      : '(config)',
    }
    
    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'
    
    SSHClass = netmiko.ssh_dispatcher(cisco_881['device_type'])
    net_connect = SSHClass(**cisco_881)

    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)

    module.prompt_initial = net_connect.find_prompt()
    net_connect.enable()
    module.enable_prompt = net_connect.find_prompt()

    module.config_mode = net_connect.config_mode()

    net_connect.send_config_from_file("config_commands.txt")

    module.exit_config_mode = net_connect.exit_config_mode()
    module.config_commands_output = net_connect.send_command('show run | inc logging buffer')
    module.exit_enable_mode = net_connect.exit_enable_mode()

    net_connect.disconnect()


def test_enable_mode():
    assert prompt_initial == EXPECTED_RESPONSES['user_exec_prompt']
    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_commands_from_file():
    assert 'logging buffered 8880' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode


def test_exit_enable_mode():
    assert EXPECTED_RESPONSES["user_exec_prompt"] in exit_enable_mode
