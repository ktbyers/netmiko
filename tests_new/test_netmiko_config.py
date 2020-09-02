#!/usr/bin/env python
import pytest


def test_ssh_connect(net_connect, commands, expected_responses):
    """
    Verify the connection was established successfully
    """
    show_version = net_connect.send_command(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_enable_mode(net_connect, commands, expected_responses):
    """
    Test entering enable mode

    Catch exception for devices that don't support enable
    """
    try:
        net_connect.enable()
        enable_prompt = net_connect.find_prompt()
        assert enable_prompt == expected_responses["enable_prompt"]
    except AttributeError:
        assert True


def test_config_mode(net_connect, commands, expected_responses):
    """
    Test enter config mode
    """
    # Behavior for devices with no config mode is to return null string
    if net_connect.config_mode() != "":
        assert net_connect.check_config_mode() is True
    else:
        assert True


def test_exit_config_mode(net_connect, commands, expected_responses):
    """
    Test exit config mode
    """
    net_connect.exit_config_mode()
    assert net_connect.check_config_mode() is False


def test_config_set(net_connect, commands, expected_responses):
    """Test sending configuration commands."""
    config_commands = commands["config"]
    support_commit = commands.get("support_commit")
    config_verify = commands["config_verification"]

    # Set to initial value and testing sending command as a string
    net_connect.send_config_set(config_commands[0])
    if support_commit:
        net_connect.commit()
    cmd_response = expected_responses.get("cmd_response_init")
    config_commands_output = net_connect.send_command(config_verify)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[0] in config_commands_output
    net_connect.send_config_set(config_commands)
    if support_commit:
        net_connect.commit()
    cmd_response = expected_responses.get("cmd_response_final")
    config_commands_output = net_connect.send_command_expect(config_verify)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[-1] in config_commands_output


def test_config_set_longcommand(net_connect, commands, expected_responses):
    """Test sending configuration commands using long commands"""
    config_commands = commands.get("config_long_command")
    config_verify = commands["config_verification"]  # noqa
    if not config_commands:
        assert True
        return
    output = net_connect.send_config_set(config_commands)  # noqa
    assert True


def test_config_hostname(net_connect, commands, expected_responses):
    hostname = "test-netmiko1"
    command = f"hostname {hostname}"
    if "arista" in net_connect.device_type:
        current_hostname = net_connect.find_prompt()[:-1]
        net_connect.send_config_set(command)
        new_hostname = net_connect.find_prompt()
        assert hostname in new_hostname
        # Reset prompt back to original value
        net_connect.set_base_prompt()
        net_connect.send_config_set(f"hostname {current_hostname}")


def test_config_from_file(net_connect, commands, expected_responses):
    """
    Test sending configuration commands from a file
    """
    config_file = commands.get("config_file")
    config_verify = commands["config_verification"]
    if config_file is not None:
        net_connect.send_config_from_file(config_file)
        config_commands_output = net_connect.send_command_expect(config_verify)
        assert expected_responses["file_check_cmd"] in config_commands_output
    else:
        assert pytest.skip()

    if "nokia_sros" in net_connect.device_type:
        net_connect.save_config()


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
