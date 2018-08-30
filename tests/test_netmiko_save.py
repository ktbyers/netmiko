#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import pytest


def test_save_base(net_connect, commands, expected_responses):
    """Test save config with no options."""
    save_verify = expected_responses['save_config']
    cmd_response = net_connect.save_config()
    print(cmd_response)
    assert save_verify in cmd_response

def test_save_confirm(net_connect, commands, expected_responses):
    """Test save config with the confirm parameter."""
    confirm = commands['save_config_confirm']
    if confirm:
        save_verify = expected_responses['save_config']
        cmd_response = net_connect.save_config()
        print(cmd_response)
        assert save_verify in cmd_response
    else:
        assert pytest.skip("No confirmation needed.")

def test_save_response(net_connect, commands, expected_responses):
    """Test save config with the confirm response parameter."""
    confirm = commands['save_config_confirm']
    confirm_response = expected_responses['save_config_response']
    if confirm and confirm_response:
        save_verify = expected_responses['save_config']
        cmd_response = net_connect.save_config()
        assert save_verify in cmd_response
    else:
        assert pytest.skip("No confirmation needed.")
