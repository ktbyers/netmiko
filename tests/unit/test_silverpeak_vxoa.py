from typing import Iterator, Optional
from unittest.mock import Mock

import pytest

from netmiko.silverpeak.silverpeak_vxoa_ssh import SilverPeakVXOASSH


@pytest.fixture
def connection(monkeypatch: pytest.MonkeyPatch) -> Iterator[SilverPeakVXOASSH]:
    connection = SilverPeakVXOASSH(host="localhost", auto_connect=False)
    monkeypatch.setattr(connection, "cleanup", Mock())
    monkeypatch.setattr(connection, "clear_buffer", Mock(return_value=""))
    monkeypatch.setattr(connection, "write_channel", Mock())
    monkeypatch.setattr("netmiko.base_connection.time.sleep", lambda seconds: None)
    try:
        yield connection
    finally:
        connection.disconnect()


@pytest.mark.parametrize("prompt", ["silver1>", "silver1#", "silver1(config) #"])
def test_find_prompt_waits_for_delayed_prompt(
    connection: SilverPeakVXOASSH, monkeypatch: pytest.MonkeyPatch, prompt: str
) -> None:
    read_channel = Mock(side_effect=["", "", "", f"\n{prompt}"])
    monkeypatch.setattr(connection, "read_channel", read_channel)

    assert connection.find_prompt() == prompt
    connection.write_channel.assert_called_once_with(connection.RETURN)
    assert read_channel.call_count == 4


@pytest.mark.parametrize("prompt", ["silver1>", "silver1#", "silver1(config) #"])
@pytest.mark.parametrize("pattern", [None, ""])
def test_find_prompt_waits_for_fragmented_prompt(
    connection: SilverPeakVXOASSH,
    monkeypatch: pytest.MonkeyPatch,
    prompt: str,
    pattern: Optional[str],
) -> None:
    read_channel = Mock(side_effect=["\n", prompt[:-1], "", prompt[-1]])
    monkeypatch.setattr(connection, "read_channel", read_channel)

    assert connection.find_prompt(pattern=pattern) == prompt
    connection.write_channel.assert_called_once_with(connection.RETURN)
    assert read_channel.call_count == 4


def test_find_prompt_preserves_explicit_pattern(
    connection: SilverPeakVXOASSH, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(connection, "read_channel", Mock(return_value="\ncustom$"))

    assert connection.find_prompt(pattern=r"\$") == "custom$"
    connection.write_channel.assert_called_once_with(connection.RETURN)
