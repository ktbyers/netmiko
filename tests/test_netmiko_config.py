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
test_save_base: verify save config with default values
test_save_confirm: verify save config with confirm
test_save_response: verify save config with response
test_save_cmd: verify save config with cmd
test_save_confirm_response: verify save config with confirm and confirm response
test_save_all: verify save config with all options
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

def test_save_base(net_connect, commands, expected_responses):
    '''
    Test save config with no options.
    '''
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config()
    assert save_verify in cmd_response

def test_save_confirm(net_connect, commands, expected_responses):
    '''
    Test save config with the confirm parameter.
    '''
    confirm = commands['save_config_confirm']
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config(confirm)
    assert save_verify in cmd_response

def test_save_response(net_connect, commands, expected_responses):
    '''
    Test save config with the confirm response parameter.
    '''
    confirm_response = commands['save_config_response']
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config(confirm_response=confirm_response)
    assert save_verify in cmd_response

def test_save_cmd(net_connect, commands, expected_responses):
    '''
    Test save config with cmd parameter.
    '''
    cmd = commands['save_config_cmd']
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config(cmd=cmd)
    assert save_verify in cmd_response

def test_save_confirm_response(net_connect, commands, expected_responses):
    '''
    Test save config with confirm and confirm response parameters
    '''
    confirm = commands['save_config_confirm']
    confirm_response = commands['save_config_response']
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config(confirm=confirm, 
                                          confirm_response=confirm_response)
    assert save_verify in cmd_response    

def test_save_all(net_connect, commands, expected_responses):
    '''
    Test the save config method with all additional parameters.
    '''
    cmd = commands['save_config_cmd'] 
    confirm = commands['save_config_confirm']
    confirm_response = commands['save_config_response']
    save_verify = expected_responses['save_config']

    cmd_response = net_connect.save_config(cmd=cmd, confirm=confirm, 
                                           confirm_response=confirm_response)
    assert save_verify in cmd_response

def test_disconnect(net_connect, commands, expected_responses):
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()


