from unittest.mock import Mock

import pytest

from netmiko.huawei.huawei import HuaweiTelnet


@pytest.mark.parametrize(
    "initial_output,read_outputs,expected_writes",
    [
        (
            "Login authentication\n\nPassword:",
            ["Login authentication\n\nPassword:", "<Huawei>"],
            ["secret\r"],
        ),
        (
            "Login:",
            ["Login:", "Password:", "<Huawei>"],
            ["admin\r\n", "secret\r"],
        ),
        (
            "Login\n",
            ["Login\n", "Password:", "<Huawei>"],
            ["admin\r\n", "secret\r"],
        ),
    ],
)
def test_huawei_telnet_login_credential_prompts(initial_output, read_outputs, expected_writes):
    connection = object.__new__(HuaweiTelnet)
    connection.username = "admin"
    connection.password = "secret"
    connection.TELNET_RETURN = "\r\n"
    connection.prompt_or_password_change = r"(?:Change now|Please choose|[\]>])"
    connection.password_change_prompt = r"(?:Change now|Please choose)"
    connection.prompt_pattern = r"[\]>]"
    connection.host = "example"
    connection.remote_conn = Mock()
    connection.read_until_pattern = Mock(side_effect=read_outputs)
    connection.write_channel = Mock()

    connection.telnet_login()

    assert [call.args[0] for call in connection.write_channel.call_args_list] == (expected_writes)
    assert connection.read_until_pattern.call_count == len(read_outputs)
