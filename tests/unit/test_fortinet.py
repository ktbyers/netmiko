import pytest
from unittest.mock import MagicMock

from netmiko.fortinet.fortinet_ssh import FortinetSSH


def make_connection(grep_output):
    """Create a FortinetSSH object without opening an SSH session."""
    conn = FortinetSSH.__new__(FortinetSSH)
    conn._send_command_str = MagicMock(return_value=grep_output)
    return conn


@pytest.mark.parametrize(
    "grep_output, expected",
    [
        # FortiOS 7.4.12 - issue #3861: 'grep Version' also returns a second line
        # ("Release Version Information: GA") which contains the substring "Version".
        (
            "Version: FortiGate-900F v7.4.12,build2902,260505 (GA.M)\n"
            "Release Version Information: GA",
            "v7_or_later",
        ),
        # FortiOS 7.4.12 - clean single-line output from 'grep Version:'
        (
            "Version: FortiGate-900F v7.4.12,build2902,260505 (GA.M)",
            "v7_or_later",
        ),
        ("Version: FortiGate-VM64 v7.0.14,build1631,230920 (interim)", "v7_or_later"),
        ("Version: FortiGate-VM64 v8.2.5,build1234,240101 (GA)", "v7_or_later"),
        ("Version: FortiGate-VM64 v6.4.15,build0000,230101 (GA)", "v6_or_earlier"),
        ("Version: FortiGate-60E v5.6.10,build0000,200101 (GA)", "v6_or_earlier"),
    ],
)
def test_determine_os_version(grep_output, expected):
    conn = make_connection(grep_output)
    assert conn._determine_os_version() == expected


def test_determine_os_version_uses_grep_version_colon():
    """Ensure the grep targets 'Version:' to avoid the extra 7.4.x line."""
    conn = make_connection("Version: FortiGate-900F v7.4.12,build2902,260505 (GA.M)")
    conn._determine_os_version()
    conn._send_command_str.assert_called_once_with(
        "get system status | grep Version:", expect_string=conn.prompt_pattern
    )


def test_determine_os_version_unexpected():
    conn = make_connection("Release Version Information: GA")
    with pytest.raises(ValueError):
        conn._determine_os_version()
