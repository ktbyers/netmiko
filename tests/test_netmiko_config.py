#!/usr/bin/env python
import ipaddress


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
        assert True is True


def test_config_mode(net_connect, commands, expected_responses):
    """
    Test enter config mode
    """
    net_connect.config_mode()
    assert net_connect.check_config_mode() == True


def test_exit_config_mode(net_connect, commands, expected_responses):
    """
    Test exit config mode
    """
    net_connect.exit_config_mode()
    assert net_connect.check_config_mode() == False


def test_command_set(net_connect, commands, expected_responses):
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
    print(config_verify)
    print(config_commands_output)
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


def test_commands_from_file(net_connect, commands, expected_responses):
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
        print("Skipping test (no file specified)...")


def test_large_acl(net_connect, acl_entries=500):
    """
    Test creating an ACL with tons of lines
    """
    if net_connect.device_type not in ["cisco_xe", "cisco_ios"]:
        return
    net_connect.send_config_set(["no ip access-list extended netmiko_test_large_acl"])
    cfg_lines = ["ip access-list extended netmiko_test_large_acl"]
    for i in range(1, acl_entries + 1):
        cfg_lines.append(
            f"permit ip host {ipaddress.ip_address('192.168.0.0') + i} any"
        )
    result = net_connect.send_config_set(cfg_lines)
    # check that the result of send_config_set returns same num lines + four lines for getting
    # into and out of config mode
    assert len(result.splitlines()) == len(cfg_lines) + 4
    verify = net_connect.send_command("show ip access-lists netmiko_test_large_acl")
    # check that length of lines in show of the acl matches lines configured
    assert len(verify.splitlines()) == len(cfg_lines)
    net_connect.send_config_set(["no ip access-list extended netmiko_test_large_acl"])
    net_connect.disconnect()


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
