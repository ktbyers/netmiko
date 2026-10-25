from collections import deque
from unittest.mock import Mock, call

import pytest

from netmiko.hp.hp_procurve import HPProcurveSSH


@pytest.mark.parametrize(
    "stale_prompt, username_prompt, verify_echo",
    [
        ("", "Please Enter Login Name: ", None),
        ("\nswitch> ", "Please Enter Login Name: ", None),
        ("", "", None),
        ("\nswitch> ", "", None),
        ("", "", False),
    ],
)
def test_enable_reads_command_echo_before_authentication(
    stale_prompt, username_prompt, verify_echo
):
    """A pending unprivileged prompt must not terminate the enable exchange."""
    connection = HPProcurveSSH(
        host="localhost",
        username="operator",
        secret="secret",
        global_cmd_verify=verify_echo,
        auto_connect=False,
    )
    connection.base_prompt = "switch"
    replies = deque()
    enabled = False

    def write(data):
        nonlocal enabled
        if data == connection.RETURN:
            replies.append("\nswitch#" if enabled else "\nswitch>")
        elif data == "enable" + connection.RETURN:
            # The old prompt may arrive before the command echo, in a separate read.
            if stale_prompt:
                replies.append(stale_prompt)
            echo = "enable\n" if verify_echo is not False else ""
            replies.append(echo + (username_prompt or "Password: "))
        elif data == "operator" + connection.RETURN:
            replies.append("operator\nPassword: ")
        elif data == "secret" + connection.RETURN:
            enabled = True
            replies.append("\nswitch#")
        else:
            pytest.fail(f"Unexpected write: {data!r}")

    connection.channel = Mock()
    connection.channel.write_channel.side_effect = write
    connection.channel.read_channel.side_effect = lambda: replies.popleft() if replies else ""

    output = connection.enable()

    assert enabled
    if verify_echo is not False:
        assert "enable" in output
    assert "switch#" in output
    expected = [call(connection.RETURN), call("enable" + connection.RETURN)]
    if username_prompt:
        expected.append(call("operator" + connection.RETURN))
    expected.extend([call("secret" + connection.RETURN), call(connection.RETURN)])
    assert connection.channel.write_channel.call_args_list == expected
