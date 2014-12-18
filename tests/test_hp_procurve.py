#!/usr/bin/env python

import pytest
import re

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'router_prompt' : 'twb-sf-hpsw1#',
        'router_enable' : 'twb-sf-hpsw1#',
        'interface_ip'  : '10.220.88.10',
        'config_mode'   : '(config)',
    }
    
    show_ver_command = 'show version'
    multiple_line_command = 'show logging'
    module.basic_command = 'show ip'
    
    SSHClass = netmiko.ssh_dispatcher(hp_procurve['device_type'])
    net_connect = SSHClass(**hp_procurve)

    module.show_version = net_connect.send_command(show_ver_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command, delay_factor=2)
    module.show_ip = net_connect.send_command(module.basic_command)

    module.router_prompt = net_connect.router_prompt

    # Enable doesn't do anything on ProCurve
    net_connect.enable()

    # Enter config mode
    module.config_mode = net_connect.config_mode()

    # Exit config mode
    module.exit_config_mode = net_connect.exit_config_mode()

    # Send a set of config commands
    config_commands = ['time timezone -420', 'time timezone -480', 
            'time daylight-time-rule Continental-US-and-Canada' ]
    net_connect.send_config_set(config_commands)

    # Verify config changes 
    module.config_commands_output = net_connect.send_command('show run')

    net_connect.disconnect()


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert 'Bottom of Log' in multiple_line_output


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'Image stamp:' in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_find_prompt():
    '''
    Verify the router prompt is detected correctly
    '''
    assert router_prompt == EXPECTED_RESPONSES['router_prompt']


def test_strip_prompt():
    '''
    Ensure the router prompt is not in the command output
    '''
    assert EXPECTED_RESPONSES['router_prompt'] not in show_ip


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


def test_enable_mode():
    assert router_prompt == EXPECTED_RESPONSES['router_enable']


def test_command_set():
    assert 'time timezone -480' in config_commands_output


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode


def test_strip_ansi_escape():
    '''
    Test that a long string comes back as expected
    '''
    assert '----  Bottom of Log : Events Listed = ' in multiple_line_output
