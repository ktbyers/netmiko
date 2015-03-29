#!/usr/bin/env python
"""
This module runs tests against Cisco IOS devices.

setup_module: setup variables for later use.

test_ssh_connect: verify ssh connectivity
test_enable_mode: verify enter enable mode
test_config_mode: verify enter config mode
test_exit_config_mode: verify exit config mode
test_command_set: verify sending a set of config commands
test_commands_from_file: verify sending a set of config commands from a file
test_exit_enable_mode: verify exit enable mode
test_disconnect: cleanly disconnect the SSH session

"""

import time


def test_ssh_connect(net_connect, commands, expected_responses):
    '''
    Verify the connection was established successfully
    '''
    show_version = net_connect.send_command(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_enable_mode(net_connect, commands, expected_responses):
    '''
    Test entering enable mode
    '''
    router_prompt = net_connect.find_prompt()
    assert router_prompt == expected_responses['router_prompt']
    net_connect.enable()
    enable_prompt = net_connect.find_prompt()
    assert enable_prompt == expected_responses['enable_prompt']


def test_config_mode(net_connect, commands, expected_responses):
    '''
    Test enter config mode
    '''
    net_connect.config_mode()
    assert expected_responses['config_mode'] in net_connect.find_prompt()


def test_exit_config_mode(net_connect, commands, expected_responses):
    '''
    Test exit config mode
    '''
    net_connect.exit_config_mode()
    assert expected_responses['config_mode'] not in net_connect.find_prompt()


def test_command_set(net_connect, commands, expected_responses):
    '''
    Test sending configuration commands
    '''
    config_commands = commands['config']
    net_connect.send_config_set(config_commands[0:1])
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert config_commands[0] in config_commands_output
    net_connect.send_config_set(config_commands)
    config_commands_output = net_connect.send_command('show run | inc logging buffer')
    assert config_commands[-1] in config_commands_output


def test_commands_from_file(net_connect, commands, expected_responses):
    '''
    Test sending configuration commands from a file
    '''
    config_file = commands.get('config_file')
    if config_file is not None:
        net_connect.send_config_from_file(config_file)
        config_commands_output = net_connect.send_command('show run | inc logging buffer')
        assert expected_responses["file_check_cmd"] in config_commands_output
    else:
        print "Skipping test"


def test_exit_enable_mode(net_connect, commands, expected_responses):
    '''
    Test exit enable mode
    '''
    exit_enable_mode = net_connect.exit_enable_mode()
    assert expected_responses["router_prompt"] in exit_enable_mode


def test_disconnect(net_connect, commands, expected_responses):
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()


