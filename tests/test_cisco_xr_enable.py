#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *

def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'enable_prompt' : 'RP/0/0/CPU0:XRv-1#',
        'base_prompt'   : 'RP/0/0/CPU0:XRv-1',
        'interface_ip'  : '169.254.254.181',
        'config_mode'   : '(config)'
    }

    show_ver_command = 'show version'
    commit_history_cmd = 'show configuration commit list'
    module.basic_command = 'show ipv4 int brief'

    SSHClass = netmiko.ssh_dispatcher(cisco_xr['device_type'])
    net_connect = SSHClass(**cisco_xr)

    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)

    net_connect.enable()
    module.enable_prompt = net_connect.find_prompt()

    current_commit_history = net_connect.send_command(commit_history_cmd)

    # get the current 10 digit commit Label ID 
    module.current_commit = current_commit_history.split('\n')[4].split()[1]
    module.config_mode = net_connect.config_mode()
    config_commands = ['logging monitor warning', 'logging buffered 30720100', 'logging console errors']
    net_connect.send_config_set(config_commands, commit=True)

    new_commit_history = net_connect.send_command(commit_history_cmd)

    # get the new 10 digit commit Label ID 
    module.new_commit = new_commit_history.split('\n')[4].split()[1]

    module.config_commands_output = net_connect.send_command("show run | inc logging")

    net_connect.disconnect()


def test_enable_mode():
    assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'logging buffered 30720100' in config_commands_output
    assert 'logging console errors' in config_commands_output
   
 
def test_commit():
    assert int(current_commit) < int(new_commit)
