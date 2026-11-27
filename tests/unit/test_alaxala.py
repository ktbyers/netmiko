from unittest.mock import Mock

import pytest

from netmiko._telnetlib.telnetlib import DO, DONT, ECHO, IAC, NAWS, SGA, TTYPE, WILL, WONT
from netmiko.alaxala import AlaxalaAx36sTelnet
from netmiko.ssh_dispatcher import CLASS_MAPPER


def test_alaxala_ax36s_telnet_registered() -> None:
    assert CLASS_MAPPER["alaxala_ax36s_telnet"] is AlaxalaAx36sTelnet


@pytest.mark.parametrize(
    "command, option, reply",
    [
        (WILL, ECHO, IAC + DO + ECHO),
        (WILL, SGA, IAC + DO + SGA),
        (WILL, TTYPE, IAC + DONT + TTYPE),
        (DO, NAWS, IAC + WONT + NAWS),
        (DO, ECHO, IAC + WONT + ECHO),
    ],
)
def test_alaxala_ax36s_telnet_options(command: bytes, option: bytes, reply: bytes) -> None:
    connection = AlaxalaAx36sTelnet.__new__(AlaxalaAx36sTelnet)
    tsocket = Mock()
    connection._process_option(tsocket, command, option)
    tsocket.sendall.assert_called_once_with(reply)


@pytest.mark.parametrize("command", [WONT, DONT])
def test_alaxala_ax36s_telnet_no_reply(command: bytes) -> None:
    connection = AlaxalaAx36sTelnet.__new__(AlaxalaAx36sTelnet)
    tsocket = Mock()
    connection._process_option(tsocket, command, ECHO)
    tsocket.sendall.assert_not_called()
