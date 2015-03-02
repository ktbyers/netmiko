#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt'  : 'openstack-rb5',
        'interface_ip' : '10.254.8.8',
    }

    show_ver_command = 'show version'
    multiple_line_command = 'show interface'
    module.basic_command = 'show system'

    SSHClass = netmiko.ssh_dispatcher(brocade_vdx['device_type'])
    net_connect = SSHClass(**brocade_vdx)

    module.show_version = net_connect.send_command(show_ver_command)
    module.multiple_line_output = net_connect.send_command(multiple_line_command)
    module.show_system = net_connect.send_command(module.basic_command)
    module.base_prompt = net_connect.base_prompt


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert 'Vlan 4095' in multiple_line_output


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'NOS' in show_version


def test_verify_send_command():
    '''
    Verify a command can be sent down the channel successfully
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_system


def test_base_prompt():
    '''
    Verify the router prompt is detected correctly
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
    assert basic_command not in show_version


def test_normalize_linefeeds():
    '''
    Ensure no '\r\n' sequences
    '''
    assert not '\r\n' in show_version


