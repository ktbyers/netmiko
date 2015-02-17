#!/usr/bin/env python

import pytest
import re

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'twb-py-lab',
        'interface_ip'  : '10.220.88.1',
        'config_mode'   : '(config)',
    }

    show_ver_command = 'show version'
    multiple_line_command = 'show version'
    module.basic_command = 'show ip'
    
    SSHClass = netmiko.ssh_dispatcher(cisco_asa['device_type'])
    net_connect = SSHClass(**cisco_asa)

    # ASA enters enable mode as part of connection (disable paging is
    # a config-mode command)
    module.base_prompt = net_connect.base_prompt

    # Test connection successful
    module.show_version = net_connect.send_command(show_ver_command)

    # Test output paging
    module.multiple_line_output = net_connect.send_command(multiple_line_command)

    # Test sending a show command
    module.show_ip = net_connect.send_command(module.basic_command)

    # Send a set of config commands
    config_commands = ['logging buffered notifications', 'logging buffered warnings', 'no logging console']
    net_connect.send_config_set(config_commands)

    # Enter/exit config mode
    module.config_mode = net_connect.config_mode()
    module.exit_config_mode = net_connect.exit_config_mode()

    # Verify config changes 
    module.config_commands_output = net_connect.send_command('show run | inc logging buffer')

    net_connect.disconnect()


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert re.search(r'Configuration register is 0x1', multiple_line_output)


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'Cisco Adaptive Security Appliance' in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_find_prompt():
    '''
    Verify the router prompt is detected correctly
    '''
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_strip_prompt():
    '''
    Ensure the router prompt is not in the command output
    '''
    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip


def test_strip_command():
    '''
    Ensure that the command that was executed does not show up in the 
    command output
    '''
    assert basic_command not in show_ip


def test_normalize_linefeeds():
    '''
    Ensure no '\r\n' sequences
    '''
    assert not '\r\n' in show_version


def test_enable_mode():
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_command_set():
    assert 'logging buffered warnings' in config_commands_output
   
 
def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
