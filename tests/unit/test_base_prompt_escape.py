import re
import subprocess
import sys
from unittest.mock import Mock

import pytest

from netmiko.base_connection import BaseConnection
from netmiko.cisco.cisco_ios import InLineTransfer
from netmiko.flexvnf.flexvnf_ssh import FlexvnfSSH
from netmiko.nokia.nokia_sros import NokiaSros


def inline_transfer_pattern(base_prompt, monkeypatch):
    """Return the pattern InLineTransfer.put_file() waits for after tclquit."""
    monkeypatch.setattr("netmiko.cisco.cisco_ios.time.sleep", lambda *args: None)
    channel = Mock(base_prompt=base_prompt)
    channel.read_until_pattern.return_value = ""
    transfer = InLineTransfer.__new__(InLineTransfer)
    transfer.ssh_ctl_chan = channel
    transfer.file_system = "flash:"
    transfer.dest_file = "test.txt"
    transfer.source_file = None
    transfer.source_config = "hostname test"
    transfer.file_size = 1
    transfer.put_file()
    kwargs = channel.read_until_pattern.call_args.kwargs
    return kwargs["pattern"], kwargs["re_flags"], "tclquit\r\n"


def nokia_config_pattern(base_prompt, monkeypatch):
    """Return the pattern NokiaSros.config_mode() waits for in MD-CLI mode."""
    captured = {}

    def fake_config_mode(self, config_command, pattern, re_flags):
        captured.update(pattern=pattern, re_flags=re_flags)
        return ""

    monkeypatch.setattr(BaseConnection, "config_mode", fake_config_mode)
    connection = NokiaSros.__new__(NokiaSros)
    connection.base_prompt = base_prompt
    connection.config_mode()
    return captured["pattern"], captured["re_flags"], "edit-config exclusive\r\n(ex)[/]\r\n"


def flexvnf_commit_pattern(base_prompt, monkeypatch):
    """Return the expect_string FlexvnfSSH.commit(and_quit=True) waits for."""
    connection = FlexvnfSSH.__new__(FlexvnfSSH)
    connection.base_prompt = base_prompt
    connection.config_mode = Mock(return_value="")
    connection._send_command_str = Mock(return_value="Commit complete.")
    connection.commit(and_quit=True)
    return connection._send_command_str.call_args.kwargs["expect_string"], 0, "Commit complete.\n"


SITES = [
    pytest.param(inline_transfer_pattern, id="cisco-inline-transfer"),
    pytest.param(nokia_config_pattern, id="nokia-sros-config-mode"),
    pytest.param(flexvnf_commit_pattern, id="flexvnf-commit"),
]


@pytest.mark.parametrize("site", SITES)
@pytest.mark.parametrize(
    "base_prompt", ["admin@R1(lab)", "admin@sw[1", "admin@r1.lab+1", "admin@(a+)+b"]
)
def test_prompt_metacharacters_match_literally(site, base_prompt, monkeypatch):
    """Prompts containing regex metacharacters must be found as literal text.

    Parentheses, brackets, and repetition characters are valid in device prompts.
    Treating them as regex syntax raises errors or fails to detect the prompt.
    """
    pattern, flags, prefix = site(base_prompt=base_prompt, monkeypatch=monkeypatch)
    output = f"{prefix}{base_prompt}# "
    assert re.search(pattern, output, flags=flags) is not None


@pytest.mark.parametrize("site", SITES)
def test_prompt_wildcard_characters_are_not_wildcards(site, monkeypatch):
    """A '.' in the prompt must match only a literal '.' character.

    Interpreting it as a wildcard could treat different text as the prompt.
    This checks the prompt is escaped, not merely tolerated by the regex parser.
    """
    pattern, flags, prefix = site(base_prompt="admin@r1.lab", monkeypatch=monkeypatch)
    assert re.search(pattern, f"{prefix}admin@r1Xlab# ", flags=flags) is None


@pytest.mark.parametrize("site", SITES)
def test_hostile_prompt_search_is_bounded(site, monkeypatch):
    """A device-chosen prompt must not cause catastrophic regex backtracking.

    The prompt '(a+)+b' followed by a long run of 'a' backtracks exponentially when
    used as a regex. The search runs in a subprocess killed after five seconds,
    so a regression fails this test instead of hanging pytest.
    """
    pattern, flags, prefix = site(base_prompt="admin@(a+)+b", monkeypatch=monkeypatch)
    search_code = (
        "import re, sys\n"
        "match = re.search(sys.argv[1], sys.stdin.read(), flags=int(sys.argv[2]))\n"
        "sys.exit(0 if match is None else 1)\n"
    )
    try:
        result = subprocess.run(
            args=[sys.executable, "-c", search_code, pattern, str(int(flags))],
            input=f"{prefix}admin@" + "a" * 64,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Prompt search exceeded the 5-second subprocess limit", pytrace=False)
    assert result.returncode == 0, result.stderr or "Hostile output matched the prompt"
