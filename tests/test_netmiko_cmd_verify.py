import pytest
from netmiko.utilities import select_cmd_verify


@select_cmd_verify
def bogus_func(obj, *args, **kwargs):
    """Function that just returns the arguments modified by the decorator."""
    return (obj, args, kwargs)


def test_cmd_verify_decorator(net_connect_cmd_verify):
    obj = net_connect_cmd_verify
    # Global False should have precedence
    assert obj.global_cmd_verify is False
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=True)
    assert kwargs["cmd_verify"] is False
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=False)
    assert kwargs["cmd_verify"] is False

    # Global True should have precedence
    obj.global_cmd_verify = True
    assert obj.global_cmd_verify is True
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=True)
    assert kwargs["cmd_verify"] is True
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=False)
    assert kwargs["cmd_verify"] is True

    # None should track the local argument
    obj.global_cmd_verify = None
    assert obj.global_cmd_verify is None
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=True)
    assert kwargs["cmd_verify"] is True
    (obj, args, kwargs) = bogus_func(net_connect_cmd_verify, cmd_verify=False)
    assert kwargs["cmd_verify"] is False

    # Set it back to proper False value (so later tests aren't messed up).
    obj.global_cmd_verify = False


def test_send_command_global_cmd_verify(
    net_connect_cmd_verify, commands, expected_responses
):
    """
    Verify a command can be sent down the channel successfully using send_command method.

    Disable cmd_verify globally.
    """
    net_connect = net_connect_cmd_verify
    if net_connect.fast_cli is True:
        assert pytest.skip()
    net_connect.clear_buffer()
    # cmd_verify should be disabled globally at this point
    assert net_connect.global_cmd_verify is False
    show_ip_alt = net_connect.send_command(commands["basic"])
    assert expected_responses["interface_ip"] in show_ip_alt
