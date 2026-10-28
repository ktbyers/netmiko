from unittest.mock import Mock

import pytest

from netmiko.arista.arista import AristaSSH


@pytest.mark.parametrize("suffix", [""] + [f"(s{digit})" for digit in range(10)])
@pytest.mark.parametrize("context", ["", "(config)", "(config-if-Et1)"])
def test_check_config_mode_supervisor_suffix(suffix: str, context: str) -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.RETURN = "\n"
    connection.write_channel = Mock()
    connection.read_until_pattern = Mock(return_value=f"switch{suffix}{context}#")

    assert connection.check_config_mode() is bool(context)
    connection.write_channel.assert_called_once_with(connection.RETURN)
    connection.read_until_pattern.assert_called_once_with(pattern=r"[>\#]")


@pytest.mark.parametrize("suffix", ["(s10)", "(sx)", "(s)"])
def test_check_config_mode_preserves_other_suffixes(suffix: str) -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.RETURN = "\n"
    connection.write_channel = Mock()
    connection.read_until_pattern = Mock(return_value=f"switch{suffix}#")

    assert connection.check_config_mode(check_string=suffix)


@pytest.mark.parametrize("suffix", [""] + [f"(s{digit})" for digit in range(10)])
@pytest.mark.parametrize("terminator", ["#", ">"])
def test_set_base_prompt_supervisor_suffix(suffix: str, terminator: str) -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.find_prompt = Mock(return_value=f"switch{suffix}{terminator}")

    assert connection.set_base_prompt() == "switch"
    assert connection.base_prompt == "switch"
    connection.find_prompt.assert_called_once_with(delay_factor=1.0, pattern=r"(?:\#|>)")


@pytest.mark.parametrize(
    "hostname, expected",
    [
        ("switch(s10)", "switch(s10)"),
        ("switch(sx)", "switch(sx)"),
        ("switch(s1)-edge", "switch(s1)-edge"),
        ("switch(s1)-edge(s2)", "switch(s1)-edge"),
    ],
)
def test_set_base_prompt_only_strips_trailing_single_digit_suffix(
    hostname: str, expected: str
) -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.find_prompt = Mock(return_value=f"{hostname}#")

    assert connection.set_base_prompt() == expected
    assert connection.base_prompt == expected


def test_set_base_prompt_forwards_arguments() -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.find_prompt = Mock(return_value="switch(s2)!")

    assert (
        connection.set_base_prompt(
            pri_prompt_terminator="!",
            alt_prompt_terminator="?",
            delay_factor=2.0,
            pattern=r"[!?]",
        )
        == "switch"
    )
    assert connection.base_prompt == "switch"
    connection.find_prompt.assert_called_once_with(delay_factor=2.0, pattern=r"[!?]")


def test_set_base_prompt_rejects_invalid_prompt() -> None:
    connection = AristaSSH.__new__(AristaSSH)
    connection.find_prompt = Mock(return_value="switch(s1)")

    with pytest.raises(expected_exception=ValueError, match="Router prompt not found"):
        connection.set_base_prompt()
