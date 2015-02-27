#!/usr/bin/env python

import pytest

import netmiko
from DEVICE_CREDS import *


def setup_module(module):

    module.EXPECTED_RESPONSES = {
        'base_prompt' : 'openstack-rb5',
        'config_mode'   : '(config)',
    }
    
    SSHClass = netmiko.ssh_dispatcher(brocade_vdx['device_type'])
    net_connect = SSHClass(**brocade_vdx)

    # Enter enable mode
    module.prompt_initial = net_connect.find_prompt()
    net_connect.enable()
    module.enable_prompt = net_connect.find_prompt()

    # Send a set of config commands
    module.config_mode = net_connect.config_mode()
    config_commands = ['logging raslog console WARNING', 'interface vlan 20', 'banner motd test_message']
    net_connect.send_config_set(config_commands)

    # Exit config mode
    module.exit_config_mode = net_connect.exit_config_mode()

    # Verify config changes 
    module.config_commands_output = net_connect.send_command('show vlan brief')

    net_connect.disconnect()


#def test_enable_mode():
    #assert prompt_initial == EXPECTED_RESPONSES['user_exec_prompt']
    #assert enable_prompt == EXPECTED_RESPONSES['enable_prompt']


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'VLAN0020' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode
