#!/usr/bin/env python
'''
Explictly use ssh_dispatcher to select SSH class
'''

import pytest

import netmiko
import time
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'pynet-rtr1',
        'interface_ip'  : '10.220.88.20'
    }
    
    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'
   
    SSHClass = netmiko.ssh_dispatcher(device_type=cisco_881['device_type']) 
    net_connect = SSHClass(**cisco_881)

    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)
    module.base_prompt = net_connect.base_prompt

    module.show_ip_alt = net_connect.send_command_expect(module.basic_command)
    module.show_version_alt = net_connect.send_command_expect(show_ver_command)

    # Test buffer clearing
    net_connect.remote_conn.sendall(show_ver_command)
    time.sleep(2)
    net_connect.clear_buffer()
    # Should not be anything there on the second pass
    module.clear_buffer_check = net_connect.clear_buffer()
    

def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert 'Configuration register is' in show_version


def test_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'Cisco IOS Software' in show_version


def test_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_send_command_expect():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip_alt


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
    assert EXPECTED_RESPONSES['base_prompt'] not in show_ip_alt


def test_strip_command():
    '''
    Ensure that the command that was executed does not show up in the 
    command output
    '''
    assert basic_command not in show_ip
    assert basic_command not in show_ip_alt


def test_normalize_linefeeds():
    '''
    Ensure no '\r\n' sequences
    '''
    assert not '\r\n' in show_version
    assert not '\r\n' in show_version_alt


def test_clear_buffer():
    '''
    Test that clearing the buffer works
    '''
    assert clear_buffer_check is None

