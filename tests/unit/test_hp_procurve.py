from unittest.mock import Mock, call

from netmiko.hp.hp_procurve import HPProcurveSSH


def test_enable_with_pending_prompt() -> None:
    """A stale prompt before the enable echo must not skip authentication."""
    connection = HPProcurveSSH(
        host="localhost",
        username="operator",
        secret="secret",
        auto_connect=False,
    )
    connection.base_prompt = "switch"
    connection.clear_buffer = Mock()
    connection.channel = Mock()
    connection.channel.read_channel.side_effect = [
        "\nswitch>",  # Initial enable-mode check.
        "\nswitch> ",  # Stale prompt arriving before the enable echo.
        "enable\n",
        "Please Enter Login Name: ",
        "operator\nPassword: ",
        "\nswitch#",
        "\nswitch#",  # Final enable-mode check.
    ]

    try:
        output = connection.enable()

        assert "enable" in output
        assert "switch#" in output
        assert connection.channel.write_channel.call_args_list == [
            call(connection.RETURN),
            call("enable" + connection.RETURN),
            call("operator" + connection.RETURN),
            call("secret" + connection.RETURN),
            call(connection.RETURN),
        ]
    finally:
        connection.disconnect()
