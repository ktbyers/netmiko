#!/usr/bin/env python


def test_save_base(net_connect, commands, expected_responses):
    """
    Test save config with no options.
    """
    save_verify = expected_responses["save_config"]

    cmd_response = net_connect.save_config()
    assert save_verify in cmd_response


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
