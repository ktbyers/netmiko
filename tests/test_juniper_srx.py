#!/usr/bin/env python

import pytest

import netmiko
import time
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt'    : 'pyclass@pynet-jnpr-srx1',
        'router_prompt'    : 'pyclass@pynet-jnpr-srx1>',
        'router_conf_mode'  : 'pyclass@pynet-jnpr-srx1#',
        'interface_ip'      : '10.220.88.39',
    }
    
    show_ver_command = 'show version'
    multiple_line_command = 'show configuration'
    module.basic_command = 'show interfaces terse'
    
    SSHClass = netmiko.ssh_dispatcher(juniper_srx['device_type'])
    net_connect = SSHClass(**juniper_srx)

    module.show_version = net_connect.send_command(show_ver_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command, delay_factor=2)
    module.show_ip = net_connect.send_command(module.basic_command)
    module.base_prompt = net_connect.base_prompt

    # Test buffer clearing
    net_connect.remote_conn.send(show_ver_command)
    time.sleep(2)
    net_connect.clear_buffer()
    # Should not be anything there on the second pass
    module.clear_buffer_check = net_connect.clear_buffer()
    

def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert 'security-zone untrust' in multiple_line_output


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'JUNOS Software Release' in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_base_prompt():
    '''
    Verify the router base_prompt is detected correctly
    '''
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_strip_prompt():
    '''
    Ensure the router prompt is not in the command output
    '''
    assert EXPECTED_RESPONSES['base_prompt'] not in show_version


def test_strip_command():
    '''
    Ensure that the command that was executed does not show up in the 
    command output
    '''
    assert basic_command not in show_ip


def test_normalize_linefeeds():
    '''
    Ensure no '\r' sequences
    '''
    assert not '\r' in show_ip


def test_clear_buffer():
    '''
    Test that clearing the buffer works
    '''
    assert clear_buffer_check is None
