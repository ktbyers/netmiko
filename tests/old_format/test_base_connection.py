#!/usr/bin/env python
'''
This module runs tests against Cisco IOS devices.

setup_module: setup variables for later use.

test_init_method: verify attributes get set properly in init
test_session_preparation: verify session_preparation method
test_establish_connection: verify SSH connection gets established
test_disable_paging: disable paging
test_set_base_prompt: verify the base prompt is properly set
test_find_prompt: verify find prompt method
test_clear_buffer: clear SSH buffer
test_send_command: send a command
test_send_command_expect: send a command using expect-like method
test_normalize_linefeeds: ensure \n is the only line termination character in output
test_disconnect: cleanly disconnect the SSH session
'''

from os import path
import time

import pytest

from netmiko import ConnectHandler
from test_utils import parse_yaml


def setup_module(module):
    '''
    Setup variables for tests.
    '''

    test_type = 'cisco_ios'

    pwd = path.dirname(path.realpath(__file__))

    responses = parse_yaml(pwd + "/etc/responses.yml")
    module.EXPECTED_RESPONSES = responses[test_type]

    commands = parse_yaml(pwd + "/etc/commands.yml")
    module.commands = commands[test_type]

    test_devices = parse_yaml(pwd + "/etc/test_devices.yml")
    module.device = test_devices[test_type]
    device['verbose'] = False

    module.net_connect = ConnectHandler(**device)


def test_init_method():
    '''
    Verify attributes assigned in __init__ method
    '''
    assert net_connect.ip == device['ip']
    assert net_connect.port == device.get('port', 22)
    assert net_connect.username == device['username']
    assert net_connect.password == device['password']
    assert net_connect.secret == device['secret']
    assert net_connect.device_type == device['device_type']
    assert net_connect.ansi_escape_codes == False
    assert net_connect.base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_session_preparation():
    '''
    Paging should be disabled and base_prompt should be set
    '''
    assert net_connect.base_prompt == EXPECTED_RESPONSES['base_prompt']
    show_version = net_connect.send_command(commands['version'])
    assert 'Configuration register is' in show_version


def test_establish_connection():
    '''
    Verify connection gets established
    '''
    show_ip = net_connect.send_command(commands['basic'])
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_disable_paging():
    '''
    Verify paging is disabled
    '''
    multiple_line_output = net_connect.send_command(commands['extended_output'])
    assert 'Configuration register is' in multiple_line_output


def test_set_base_prompt():
    '''
    Verify the set_base_prompt() method
    '''
    assert net_connect.base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_find_prompt():
    '''
    Verify the find_prompt() method returns the current prompt
    '''
    assert net_connect.find_prompt() == EXPECTED_RESPONSES['router_prompt']


def test_clear_buffer():
    '''
    Verify the clear_buffer() method removes any outstanding data from the SSH channel
    '''

    # Manually send a command down the channel so that data needs read.
    net_connect.remote_conn.sendall(commands["basic"] + '\n')
    time.sleep(2)
    net_connect.clear_buffer()

    # Should not be anything there on the second pass
    clear_buffer_check = net_connect.clear_buffer()
    assert clear_buffer_check is None


def test_send_command():
    '''
    Verify send_command() method with default parameters works properly
    Verify send_command() with additional delay works properly
    Verify send_command() with less delay works properly
    Verify send_command() with lower max_loops works properly
    '''

    basic_command = commands.get('basic')
    send_command_std = net_connect.send_command(basic_command)
    send_command_slow = net_connect.send_command(basic_command, delay_factor=2)
    send_command_fast = net_connect.send_command(basic_command, delay_factor=.25)
    send_command_max_loops = net_connect.send_command(basic_command, max_loops=10)
    strip_prompt_true = send_command_std
    strip_prompt_false = net_connect.send_command(basic_command,
        strip_prompt=False)
    strip_command_true = send_command_std
    strip_command_false = net_connect.send_command(basic_command,
        strip_command=False)

    assert EXPECTED_RESPONSES['interface_ip'] in send_command_std
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_slow
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_fast
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_max_loops
    assert EXPECTED_RESPONSES['base_prompt'] not in strip_prompt_true
    assert EXPECTED_RESPONSES['base_prompt'] in strip_prompt_false
    assert basic_command not in strip_command_true
    assert basic_command in strip_command_false


def test_send_command_expect():
    '''
    Verify send_command_expect() method with default parameters works properly
    Verify send_command_expect() method with a different expect string
    Verify send_command_expect() with additional delay works properly
    Verify send_command_expect() with less delay works properly
    Verify send_command_expect() with lower max_loops works properly
    '''

    basic_command = commands.get('basic')
    cmd_expect_std = net_connect.send_command_expect(basic_command)
    cmd_expect_short = net_connect.send_command_expect(basic_command, 
        expect_string=commands.get("interface_name"))
    cmd_expect_slow = net_connect.send_command_expect(basic_command, delay_factor=2)
    cmd_expect_fast = net_connect.send_command_expect(basic_command, delay_factor=.25)
    cmd_expect_max_loops = net_connect.send_command_expect(basic_command, max_loops=10)
    expect_strip_prompt_true = cmd_expect_std
    expect_strip_prompt_false = net_connect.send_command_expect(basic_command,
        strip_prompt=False)
    expect_strip_command_true = cmd_expect_std
    expect_strip_command_false = net_connect.send_command_expect(basic_command,
        strip_command=False)

    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_std
#    assert EXPECTED_RESPONSES['interface_ip'] not in cmd_expect_short
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_slow
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_fast
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_max_loops
    assert EXPECTED_RESPONSES['base_prompt'] not in expect_strip_prompt_true
    assert EXPECTED_RESPONSES['base_prompt'] in expect_strip_prompt_false
    assert basic_command not in expect_strip_command_true
    assert basic_command in expect_strip_command_false


def test_normalize_linefeeds():
    '''
    Verify that '\r\n' are converted to '\n'
    '''
    show_ip = net_connect.send_command(commands['basic'])
    net_connect.remote_conn.sendall('show ip int brief\n')
    time.sleep(1)
    raw_output = net_connect.clear_buffer()

    assert '\r\n' in raw_output
    assert '\r\n' not in show_ip


def test_disconnect():
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()
