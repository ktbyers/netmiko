from typing import Callable, Optional

import pytest

from netmiko.exceptions import ReadTimeout
from netmiko.tplink.tplink_jetstream import TPLinkJetStreamBase


class FakeChannel:
    def __init__(
        self,
        clock: Callable[[], float],
        response_delays: list[Optional[float]],
    ) -> None:
        self.clock = clock
        self.response_delays = response_delays
        self.pending_responses: list[tuple[float, str]] = []
        self.writes: list[str] = []

    def write_channel(self, data: str) -> None:
        self.writes.append(data)
        if data != "\r\n":
            return
        response_index = len(self.writes) - 1
        if response_index < len(self.response_delays):
            delay = self.response_delays[response_index]
            if delay is not None:
                self.pending_responses.append((self.clock() + delay, "\r\nswitch1#"))

    def read_channel(self) -> str:
        ready = [item for item in self.pending_responses if item[0] <= self.clock()]
        if not ready:
            return ""
        response = min(ready, key=lambda item: item[0])
        self.pending_responses.remove(response)
        return response[1]


def make_connection(
    monkeypatch: pytest.MonkeyPatch,
    response_delays: list[Optional[float]],
) -> tuple[TPLinkJetStreamBase, FakeChannel, list[float]]:
    clock = [0.0]
    monkeypatch.setattr("netmiko.base_connection.time.time", lambda: clock[0])
    monkeypatch.setattr(
        "netmiko.tplink.tplink_jetstream.time.sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )

    channel = FakeChannel(clock=lambda: clock[0], response_delays=response_delays)
    connection = object.__new__(TPLinkJetStreamBase)
    connection.RETURN = "\r\n"
    connection.RESPONSE_RETURN = "\n"
    connection.read_timeout_override = None
    connection._read_buffer = ""
    connection.select_delay_factor = lambda delay_factor: 0.1
    connection.clear_buffer = lambda: ""
    connection.write_channel = channel.write_channel
    connection.read_channel = channel.read_channel
    return connection, channel, clock


def test_find_prompt_uses_one_return_for_fast_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    connection, channel, _ = make_connection(monkeypatch=monkeypatch, response_delays=[0.01])

    assert connection.find_prompt() == "switch1#"
    assert channel.writes == ["\r\n"]


def test_find_prompt_waits_for_delayed_prompt_with_one_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection, channel, _ = make_connection(monkeypatch=monkeypatch, response_delays=[0.06])

    assert connection.find_prompt() == "switch1#"
    assert channel.writes == ["\r\n"]
    assert channel.pending_responses == []
    channel.pending_responses.append(
        (0.0, "show running-config\r\n! complete configuration\r\nswitch1#")
    )
    command_output = connection.read_until_pattern(pattern=r"switch1#", read_timeout=1.0)
    assert "! complete configuration" in command_output
    assert command_output.endswith("switch1#")


def test_find_prompt_raises_when_response_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection, channel, clock = make_connection(monkeypatch=monkeypatch, response_delays=[None])

    with pytest.raises(ReadTimeout, match="Pattern not detected"):
        connection.find_prompt()

    assert channel.writes == ["\r\n"]
    assert clock[0] >= 10.0


@pytest.mark.parametrize("prompt", ["switch1>", "switch1#", "switch1(config)#"])
@pytest.mark.parametrize("pattern", [None, ""])
def test_find_prompt_waits_for_fragmented_prompt(
    monkeypatch: pytest.MonkeyPatch, prompt: str, pattern: Optional[str]
) -> None:
    connection, channel, _ = make_connection(monkeypatch=monkeypatch, response_delays=[None])
    channel.pending_responses.extend([(0.01, "\r\n"), (0.03, prompt[:-1]), (0.06, prompt[-1])])

    assert connection.find_prompt(pattern=pattern) == prompt
    assert channel.writes == ["\r\n"]
    assert channel.pending_responses == []


def test_find_prompt_preserves_explicit_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    connection, channel, _ = make_connection(monkeypatch=monkeypatch, response_delays=[None])
    channel.pending_responses.append((0.01, "\r\ncustom$"))

    assert connection.find_prompt(pattern=r"\$") == "custom$"
    assert channel.writes == ["\r\n"]
