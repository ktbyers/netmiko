#!/usr/bin/env python

import pytest
import re

from netmiko import ConnectHandler
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'device_type'   : 'BIG-IP',
        'pool_name'     : 'Ltm::Pool: TEST',
    }
    
    show_sys_command = 'tmsh show sys version'
    multiple_line_command = 'tmsh show sys log ltm'
    module.basic_command = 'tmsh show ltm pool TEST'
    
    net_connect = ConnectHandler(**f5_ltm_1)
    module.show_version = net_connect.send_command(show_sys_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command, delay_factor=2)
    module.show_pool = net_connect.send_command(module.basic_command)


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert re.search(r'warning f5-inova', multiple_line_output)


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert EXPECTED_RESPONSES['device_type'] in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['pool_name'] in show_pool


def test_strip_command():
    '''
    Ensure that the command that was executed does not show up in the 
    command output
    '''
    assert basic_command not in show_pool


def test_normalize_linefeeds():
    '''
    Ensure no '\r\n' sequences
    '''
    assert not '\r\n' in show_version
