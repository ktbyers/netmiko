#!/usr/bin/env python
import re
import pytest
from netmiko import ConfigInvalidException
from netmiko import ReadTimeout


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
    config_mode_command = commands.get("config_mode_command")

    if config_mode_command is not None:
        if net_connect.config_mode(config_command=config_mode_command) != "":
            assert net_connect.check_config_mode() is True
    elif net_connect.config_mode() != "":
        assert net_connect.check_config_mode() is True
    else:
        pytest.skip("Platform doesn't support config mode.")


def test_exit_config_mode(net_connect, commands, expected_responses):
    """Test exit config mode."""
    if net_connect._config_mode:
        net_connect.exit_config_mode()
        assert net_connect.check_config_mode() is False
    else:
        pytest.skip("Platform doesn't support config mode.")


def test_config_set(net_connect, commands, expected_responses):
    """Test sending configuration commands."""

    config_commands = commands["config"]
    config_mode_command = commands.get("config_mode_command")
    support_commit = commands.get("support_commit")
    config_verify = commands["config_verification"]

    # Set to initial value and testing sending command as a string
    net_connect.send_config_set(
        config_mode_command=config_mode_command,
        config_commands=config_commands[0],
    )

    if support_commit:
        net_connect.commit()
    cmd_response = expected_responses.get("cmd_response_init")
    config_commands_output = net_connect.send_command(config_verify)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[0] in config_commands_output

    # Test that something has changed.
    net_connect.send_config_set(
        config_commands=config_commands,
        config_mode_command=config_mode_command,
    )

    if support_commit:
        net_connect.commit()
    cmd_response = expected_responses.get("cmd_response_final")
    config_commands_output = net_connect.send_command_expect(config_verify)
    if cmd_response:
        assert cmd_response in config_commands_output
    else:
        assert config_commands[-1] in config_commands_output


def test_config_set_generator(net_connect, commands, expected_responses):
    """Test sending configuration commands as a generator."""

    config_commands = commands["config"]
    # Make a generator out of the config commands (to verify no issues with generators)
    config_commands_gen = (cmd for cmd in config_commands)
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

    # Send the config commands as a generator
    net_connect.send_config_set(config_commands_gen)
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
        net_connect.set_base_prompt()


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


def test_config_error_pattern(net_connect, commands, expected_responses):
    """
    Raise exception when config_error_str is present in output
    """
    error_pattern = commands.get("error_pattern")
    if error_pattern is None:
        pytest.skip("No error_pattern defined.")
    config_base = commands.get("config")
    config_err = commands.get("invalid_config")
    config_list = config_base + [config_err]

    # Should not raise an exception since error_pattern not specified
    net_connect.send_config_set(config_commands=config_list)

    if config_list and error_pattern:
        with pytest.raises(ConfigInvalidException):
            net_connect.send_config_set(
                config_commands=config_list, error_pattern=error_pattern
            )

        # Try it with cmd_verify=True also
        with pytest.raises(ConfigInvalidException):
            net_connect.send_config_set(
                config_commands=config_list,
                error_pattern=error_pattern,
                cmd_verify=True,
            )

    else:
        print("Skipping test: no error_pattern supplied.")


def test_banner(net_connect, commands, expected_responses):
    """
    Banner configuration has a special exclusing where cmd_verify is dynamically
    disabled so make sure it works.
    """
    # Make sure banner comes in as separate lines
    banner = commands.get("banner")
    if banner is None:
        pytest.skip("No banner defined.")
    # Make sure banner comes in as separate lines
    banner = banner.splitlines()
    config_base = commands.get("config")
    config_list = config_base + banner

    # Remove any existing banner
    net_connect.send_config_set("no banner login")

    # bypass_commands="" should fail as cmd_verify will be True
    with pytest.raises(ReadTimeout) as e:  # noqa
        net_connect.send_config_set(config_commands=config_list, bypass_commands="")

    # Recover from send_config_set failure. The "%" is to finish the failed banner.
    net_connect.write_channel("%\n")
    net_connect.exit_config_mode()

    net_connect.send_config_set(config_commands=config_list)
    show_run = net_connect.send_command("show run | inc banner log")
    assert "banner login" in show_run

    net_connect.send_config_set("no banner login")


def test_global_cmd_verify(net_connect, commands, expected_responses):
    """
    Banner configuration has a special exclusing where cmd_verify is dynamically
    disabled so make sure it works.
    """

    # Make sure banner comes in as separate lines
    banner = commands.get("banner")
    if banner is None:
        pytest.skip("No banner defined.")
    # Make sure banner comes in as separate lines
    banner = banner.splitlines()
    config_base = commands.get("config")
    config_list = config_base + banner

    # Remove any existing banner
    net_connect.send_config_set("no banner login")

    # bypass_commands="" should fail as cmd_verify will be True
    with pytest.raises(ReadTimeout) as e:  # noqa
        net_connect.send_config_set(config_commands=config_list, bypass_commands="")

    # Recover from send_config_set failure. The "%" is to finish the failed banner.
    net_connect.write_channel("%\n")
    net_connect.exit_config_mode()

    net_connect.global_cmd_verify = False
    # Should work now as global_cmd_verify is False
    net_connect.send_config_set(config_commands=config_list, bypass_commands="")
    show_run = net_connect.send_command("show run | inc banner log")
    assert "banner login" in show_run

    net_connect.send_config_set("no banner login")


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    if net_connect.host in ["cisco3.lasthop.io", "iosxr3.lasthop.io"]:
        hostname = net_connect.send_command("show run | inc hostname")
        if re.search("cisco3.*long", hostname):
            net_connect.send_config_set("hostname cisco3")
        elif re.search("iosxr3.*long", hostname):
            net_connect.send_config_set("hostname iosxr3")
            net_connect.commit()
            net_connect.exit_config_mode()
    net_connect.disconnect()
