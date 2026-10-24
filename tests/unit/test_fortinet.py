from unittest.mock import Mock

import pytest

from netmiko.fortinet.fortinet_ssh import FortinetSSH


FORTINET_VERSION_OUTPUTS = [
    (
        "Version: FortiGate-900F v7.4.12,build2902,260505 (GA.M)\n"
        "Release Version Information: GA\n",
        "v7_or_later",
    ),
    (
        "Version: FortiGate-101F v7.0.11,build0489,230314 (GA.M)\n"
        "Release Version Information: GA\n",
        "v7_or_later",
    ),
    (
        "Version: FortiGate-VM64-KVM v7.4.1,build2463,230830 (GA.F)\n"
        "Release Version Information: GA\n",
        "v7_or_later",
    ),
    (
        "Version: FortiGate-900G v7.6.5,build3651...\nLast reboot reason: warm reboot\n",
        "v7_or_later",
    ),
    (
        "Version: FortiGate-60F v6.4.6,build8755,220121 (GA)\nRelease Version Information: GA\n",
        "v6_or_earlier",
    ),
    ("Version: FortiGate-30E v6.2.4,build1112,200511 (GA)\n", "v6_or_earlier"),
    ("Version                         : v7.6.7-build3737 260601 (GA.M)\n", "v7_or_later"),
]


@pytest.mark.parametrize("output, expected_version", FORTINET_VERSION_OUTPUTS)
def test_determine_os_version(output: str, expected_version: str) -> None:
    connection = FortinetSSH.__new__(FortinetSSH)
    send_command = Mock(return_value=output)
    connection._send_command_str = send_command

    assert connection._determine_os_version() == expected_version
    send_command.assert_called_once_with(
        "get system status | grep Version",
        expect_string=FortinetSSH.prompt_pattern,
    )
