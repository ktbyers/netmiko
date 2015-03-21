import pytest
from DEVICE_CREDS import *
from netmiko import ConnectHandler


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'n7k1',
        'interface_ip'  : '10.3.3.245'
    }

    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'

    net_connect = ConnectHandler(**cisco_nxos)
    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)
    module.base_prompt = net_connect.base_prompt


def test_disable_paging():
    '''
    Verify paging is disabled by looking for string after when paging would
    normally occur
    '''
    assert 'Core Plugin, Ethernet Plugin' in show_version


def test_verify_ssh_connect():
    '''
    Verify the connection was established successfully
    '''
    assert 'Cisco Nexus Operating System' in show_version


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
    Ensure no '\r' sequences
    '''
    assert not '\r' in show_version


