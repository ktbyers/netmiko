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
test_disconnect: cleanly disconnect the SSH session

"""

from __future__ import print_function
from __future__ import unicode_literals


def test_ssh_connect(net_connect, commands, expected_responses):
    '''
    Verify the connection was established successfully
    '''
    show_version = net_connect.send_command(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_enable_mode(net_connect, commands, expected_responses):
    '''
    Test entering enable mode

    Catch exception for devices that don't support enable
    '''
    try:
        net_connect.enable()
        enable_prompt = net_connect.find_prompt()
        assert enable_prompt == expected_responses['enable_prompt']
    except AttributeError:
        assert True == True


def test_config_mode(net_connect, commands, expected_responses):
    '''
    Test enter config mode
    '''
    net_connect.config_mode()
    assert net_connect.check_config_mode() == True


def test_exit_config_mode(net_connect, commands, expected_responses):
    '''
    Test exit config mode
    '''
    net_connect.exit_config_mode()
    assert net_connect.check_config_mode() == False

def test_command_set(net_connect, commands, expected_responses):
    """Test sending configuration commands."""
    config_commands = commands['config']
    support_commit = commands.get('support_commit')
    config_verify = commands['config_verification']

    # Set to initial value and testing sending command as a string
    net_connect.send_config_set(config_commands[0])
    if support_commit:
        net_connect.commit()

    cmd_response = expected_responses.get('cmd_response_init')
    config_commands_output = net_connect.send_command(config_verify)
    print(config_verify)
    print(config_commands_output)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[0] in config_commands_output

    net_connect.send_config_set(config_commands)
    if support_commit:
        net_connect.commit()

    cmd_response = expected_responses.get('cmd_response_final')
    config_commands_output = net_connect.send_command_expect(config_verify)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[-1] in config_commands_output


def test_commands_from_file(net_connect, commands, expected_responses):
    '''
    Test sending configuration commands from a file
    '''
    config_file = commands.get('config_file')
    config_verify = commands['config_verification']
    if config_file is not None:
        net_connect.send_config_from_file(config_file)
        config_commands_output = net_connect.send_command_expect(config_verify)
        assert expected_responses["file_check_cmd"] in config_commands_output
    else:
        print("Skipping test (no file specified)...",)


def test_disconnect(net_connect, commands, expected_responses):
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()


