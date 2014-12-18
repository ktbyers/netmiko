#!/usr/bin/env python

import pytest
import re

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'router_prompt' : 'sf-arista-sw4>',
        'router_enable' : 'sf-arista-sw4#',
        'interface_ip'  : '10.220.88.31'
    }
    
    show_ver_command = 'show version'
    multiple_line_command = 'show logging'
    module.basic_command = 'show ip int brief'
    
    SSHClass = netmiko.ssh_dispatcher(arista_veos_sw['device_type'])
    net_connect = SSHClass(**arista_veos_sw)
    module.show_version = net_connect.send_command(show_ver_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command, delay_factor=2)
    module.show_ip = net_connect.send_command(module.basic_command)
    module.router_prompt = net_connect.router_prompt


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert re.search(r'ztp.*debugging', multiple_line_output)


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'Arista' in show_version


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
    '''
    assert not '\r\n' in show_version


