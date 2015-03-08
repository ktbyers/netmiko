#!/usr/bin/env python

import pytest

import netmiko
import time
from DEVICE_CREDS import *


def setup_module(module):
    
    module.EXPECTED_RESPONSES = {
        'base_prompt'     : 'pyclass@pynet-jnpr-srx1',
        'router_prompt'     : 'pyclass@pynet-jnpr-srx1>',
        'router_conf_mode'  : 'pyclass@pynet-jnpr-srx1#',
        'interface_ip'      : '10.220.88.39',
        'config_mode'       : '[edit',
    }
    
    show_ver_command = 'show version'
    multiple_line_command = 'show configuration'
    module.basic_command = 'show interfaces terse'
    
    SSHClass = netmiko.ssh_dispatcher(juniper_srx['device_type'])
    net_connect = SSHClass(**juniper_srx)
    
    module.show_version = net_connect.send_command(show_ver_command)
    module.show_ip = net_connect.send_command(module.basic_command)

    module.base_prompt_initial = net_connect.base_prompt
    module.config_mode = net_connect.config_mode()
    module.base_prompt = net_connect.base_prompt

    config_commands = [
        'set system syslog archive size 110k files 3',
        'set system syslog archive size 120k files 3',
        'set system time-zone America/New_York',
    ]
    net_connect.send_config_set(config_commands, commit=True)

    module.exit_config_mode = net_connect.exit_config_mode()

    module.config_commands_output = net_connect.send_command('show configuration | match time-zone')

    # Test a manual commit
    net_connect.config_mode()
    net_connect.send_command('set system time-zone America/Los_Angeles')
    net_connect.commit()
    net_connect.exit_config_mode()
    module.manual_commit = net_connect.send_command('show configuration | match time-zone')

    # Test that prompt is stripped correctly from config mode
    net_connect.config_mode()
    net_connect.send_command('edit services')
    module.show_version_from_config = net_connect.send_command('run show version')
    net_connect.exit_config_mode()

    net_connect.disconnect()


def test_config_mode():
    assert EXPECTED_RESPONSES['config_mode'] in config_mode


def test_command_set():
    assert 'time-zone America/New_York' in config_commands_output
   
 
def test_exit_config_mode():
    assert not EXPECTED_RESPONSES['config_mode'] in exit_config_mode


def test_manual_commit():
    assert 'time-zone America/Los_Angeles' in manual_commit


def test_edit_context_stripped():
    '''
    Verify [edit] is properly stripped for show commands in config mode
    '''

    assert '[edit' not in show_version_from_config
