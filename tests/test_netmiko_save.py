#!/usr/bin/env python


def test_save_base(net_connect, commands, expected_responses):
    """
    Test save config with no options.
    """
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config()
    assert save_verify in cmd_response


def test_save_confirm(net_connect, commands, expected_responses):
    """
    Test save config with the confirm parameter.
    """
    confirm = commands["save_config_confirm"]
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config(confirm)
    assert save_verify in cmd_response


def test_save_response(net_connect, commands, expected_responses):
    """
    Test save config with the confirm response parameter.
    """
    confirm_response = commands["save_config_response"]
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config(confirm_response=confirm_response)
    assert save_verify in cmd_response


def test_save_cmd(net_connect, commands, expected_responses):
    """
    Test save config with cmd parameter.
    """
    cmd = commands["save_config_cmd"]
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config(cmd=cmd)
    assert save_verify in cmd_response


def test_save_confirm_response(net_connect, commands, expected_responses):
    """
    Test save config with confirm and confirm response parameters
    """
    confirm = commands["save_config_confirm"]
    confirm_response = commands["save_config_response"]
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config(
        confirm=confirm, confirm_response=confirm_response
    )
    assert save_verify in cmd_response


def test_save_all(net_connect, commands, expected_responses):
    """
    Test the save config method with all additional parameters.
    """
    cmd = commands["save_config_cmd"]
    confirm = commands["save_config_confirm"]
    confirm_response = commands["save_config_response"]
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config(
        cmd=cmd, confirm=confirm, confirm_response=confirm_response
    )
    assert save_verify in cmd_response


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
