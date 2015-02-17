#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *

def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt'   : 'n7k1',
        'interface_ip'  : '10.3.3.245',
        'config_mode'   : '(config)'
    }


    show_ver_command = 'show version'
    module.basic_command = 'show ip int brief'

    SSHClass = netmiko.ssh_dispatcher(cisco_nxos['device_type'])
    net_connect = SSHClass(**cisco_nxos)
    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)

    module.base_prompt_initial = net_connect.base_prompt
    net_connect.enable()
    module.base_prompt = net_connect.base_prompt

    module.config_mode = net_connect.config_mode()

    config_commands = ['logging monitor 3', 'logging monitor 7', 'no logging console']
    net_connect.send_config_set(config_commands)

    module.exit_config_mode = net_connect.exit_config_mode()

    module.config_commands_output = net_connect.send_command("show run | inc 'logging monitor'")

    net_connect.disconnect()


def test_enable_mode():
    assert base_prompt_initial == EXPECTED_RESPONSES['base_prompt']
    assert base_prompt == EXPECTED_RESPONSES['base_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'logging monitor 7' in config_commands_output


def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
