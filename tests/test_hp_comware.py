#!/usr/bin/env python

import pytest
import re

from netmiko import ConnectHandler
from DEVICE_CREDS import *

def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt'   : 'vsr1000',
        'router_prompt' : '<vsr1000>',
        'interface_ip'  : '192.168.112.11',
        'config_mode'   : '[vsr1000]',
    }
    
    show_ver_command = 'display version'
    multiple_line_command = 'display logbuffer'
    module.basic_command = 'display ip interface brief'
    
    net_connect = ConnectHandler(**hp_comware)

    module.show_version = net_connect.send_command(show_ver_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command, delay_factor=2)
    module.show_ip = net_connect.send_command(module.basic_command)

    module.base_prompt = net_connect.base_prompt

    # Enter config mode
    module.config_mode = net_connect.config_mode()
    
        # Exit config mode
    module.exit_config_mode = net_connect.exit_config_mode()

    # Send a set of config commands
    config_commands = ['vlan 3000', 'name 3000-test']
    net_connect.send_config_set(config_commands)

    # Verify config changes 
    module.config_commands_output = net_connect.send_command('display vlan 3000')
    
    # Undo config changes 
    net_connect.send_command('undo vlan 3000')

    net_connect.disconnect()


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert not '---- More ----' in multiple_line_output


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'HP Comware Software' in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_base_prompt():
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
    Ensure no '\n\r' sequences for HP
    '''
    assert not '\r\n' in show_version
    assert not '\n\r' in show_version


def test_command_set():
    assert 'Name: 3000-test' in config_commands_output


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode

