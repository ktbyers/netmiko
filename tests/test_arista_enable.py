#!/usr/bin/env python

from os import path
import time

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

#    module.EXPECTED_RESPONSES = {
#        'base_prompt' : 'pynet-sw4',
#        'user_exec_prompt' : 'pynet-sw4>',
#        'enable_prompt' : 'pynet-sw4#',
#        'interface_ip'  : '10.220.88.31',
#        'config_mode'   : '(config)',
#    }
#    
#    net_connect = ConnectHandler(**arista_veos_sw)
#
#    # Enter enable mode
#    module.prompt_initial = net_connect.find_prompt()
#    net_connect.enable()
#    module.enable_prompt = net_connect.find_prompt()
#
#    # Send a set of config commands
#    module.config_mode = net_connect.config_mode()
#    config_commands = ['logging buffered 20000', 'logging buffered 20010', 'no logging console']
#    net_connect.send_config_set(config_commands)
#
#    # Exit config mode
#    module.exit_config_mode = net_connect.exit_config_mode()
#
#    # Verify config changes 
#    module.config_commands_output = net_connect.send_command('show run | inc logging buffer')
#
#    net_connect.disconnect()


def test_enable_mode():
    assert prompt_initial == EXPECTED_RESPONSES['user_exec_prompt']
    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


#def test_config_mode():
#    assert EXPECTED_RESPONSES['config_mode'] in config_mode
#
#
#def test_command_set():
#    assert 'logging buffered 20010' in config_commands_output
#   
# 
#def test_exit_config_mode():
#    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
