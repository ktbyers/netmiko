#!/usr/bin/env python

import pytest

import netmiko
import time
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'pynet-rtr1',
        'current_prompt' : 'pynet-rtr1>',
        'interface_ip'  : '10.220.88.20'
    }
    
    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'
    
    SSHClass = netmiko.ssh_dispatcher(cisco_881['device_type'])
    net_connect = SSHClass(**cisco_881)

    module.ip_addr = net_connect.ip
    module.port = net_connect.port
    module.username = net_connect.username
    module.password = net_connect.password
    module.secret = net_connect.secret
    module.device_type = net_connect.device_type
    module.ansi_escape_codes = net_connect.ansi_escape_codes
    module.base_prompt_init = net_connect.base_prompt

    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)
    module.base_prompt = net_connect.base_prompt

    module.base_prompt_manual = net_connect.set_base_prompt()

    module.current_prompt = net_connect.find_prompt()

    # Manually send a command down the channel to verify clear buffer works
    net_connect.remote_conn.send('show ip int brief\n')
    time.sleep(1)
    module.raw_output = net_connect.clear_buffer()
    module.clear_buffer = net_connect.clear_buffer()

    # send_command() parameters
    module.send_command_std = net_connect.send_command(module.basic_command)
    module.send_command_slow = net_connect.send_command(module.basic_command, delay_factor=2)
    module.send_command_fast = net_connect.send_command(module.basic_command, delay_factor=.25)
    module.send_command_max_loops = net_connect.send_command(module.basic_command, max_loops=10)
    module.strip_prompt_true = module.send_command_std
    module.strip_prompt_false = net_connect.send_command(module.basic_command,
        strip_prompt=False)
    module.strip_command_true = module.send_command_std
    module.strip_command_false = net_connect.send_command(module.basic_command,
        strip_command=False)

    # send_command_expect() parameters
    module.cmd_expect_std = net_connect.send_command_expect(module.basic_command)
    module.cmd_expect_short = net_connect.send_command_expect(module.basic_command, expect_string="FastEthernet2")
    module.cmd_expect_slow = net_connect.send_command_expect(module.basic_command, delay_factor=2)
    module.cmd_expect_fast = net_connect.send_command_expect(module.basic_command, delay_factor=.25)
    module.cmd_expect_max_loops = net_connect.send_command_expect(module.basic_command, max_loops=10)
    module.expect_strip_prompt_true = module.cmd_expect_std
    module.expect_strip_prompt_false = net_connect.send_command_expect(module.basic_command,
        strip_prompt=False)
    module.expect_strip_command_true = module.cmd_expect_std
    module.expect_strip_command_false = net_connect.send_command_expect(module.basic_command,
        strip_command=False)


def test_init_method():
    '''
    Verify attributes assigned in __init__ method
    '''
    assert ip_addr == cisco_881['ip']
    assert port == 22
    assert username == cisco_881['username']
    assert password == cisco_881['password']
    assert secret == cisco_881['secret']
    assert device_type == cisco_881['device_type']
    assert ansi_escape_codes == False
    assert base_prompt_init == EXPECTED_RESPONSES['base_prompt']


def test_session_preparation():
    '''
    Paging should be disabled and base_prompt should be set
    '''
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']
    assert 'Configuration register is' in show_version


def test_establish_connection():
    '''
    Verify connection gets established
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in show_ip


def test_disable_paging():
    '''
    Verify paging is disabled
    '''
    assert 'Configuration register is' in show_version


def test_set_base_prompt():
    '''
    Verify the set_base_prompt() method
    '''
    assert base_prompt_manual == EXPECTED_RESPONSES['base_prompt']


def test_find_prompt():
    '''
    Verify the find_prompt() method returns the current prompt
    '''
    assert current_prompt == EXPECTED_RESPONSES['current_prompt']


def test_clear_buffer():
    '''
    Verify the clear_buffer() method removes any outstanding data from the SSH channel
    '''
    assert clear_buffer is None


def test_send_command():
    '''
    Verify send_command() method with default parameters works properly
    Verify send_command() with additional delay works properly
    Verify send_command() with less delay works properly
    Verify send_command() with lower max_loops works properly
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_std
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_slow
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_fast
    assert EXPECTED_RESPONSES['interface_ip'] in send_command_max_loops


def test_send_command_expect():
    '''
    Verify send_command_expect() method with default parameters works properly
    Verify send_command_expect() method with a different expect string
    Verify send_command_expect() with additional delay works properly
    Verify send_command_expect() with less delay works properly
    Verify send_command_expect() with lower max_loops works properly
    '''
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_std
#    assert EXPECTED_RESPONSES['interface_ip'] not in cmd_expect_short
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_slow
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_fast
    assert EXPECTED_RESPONSES['interface_ip'] in cmd_expect_max_loops


def test_strip_prompt():
    '''
    Verify the trailing prompt is stripped off the output
    '''
    assert EXPECTED_RESPONSES['base_prompt'] not in strip_prompt_true
    assert EXPECTED_RESPONSES['base_prompt'] in strip_prompt_false
    assert EXPECTED_RESPONSES['base_prompt'] not in expect_strip_prompt_true
    assert EXPECTED_RESPONSES['base_prompt'] in expect_strip_prompt_false


def test_strip_command():
    '''
    Verify the leading command is stripped off the output
    '''
    assert basic_command not in strip_command_true
    assert basic_command in strip_command_false
    assert basic_command not in expect_strip_command_true
    assert basic_command in expect_strip_command_false


def test_normalize_linefeeds():
    '''
    Verify that '\r\n' are converted to '\n'
    '''
    assert '\r\n' in raw_output
    assert '\r\n' not in show_ip
