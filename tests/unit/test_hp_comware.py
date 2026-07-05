import pytest

from netmiko.hp.hp_comware import HPComwareBase


class FakeHPComwareConnection(HPComwareBase):
    def __init__(self):
        pass


@pytest.mark.parametrize("auto_find_prompt", [True, False])
def test_hp_comware_prompt_handler_clear_buffer(monkeypatch, auto_find_prompt):
    connection = FakeHPComwareConnection()
    calls = []

    def fake_find_prompt():
        calls.append("find_prompt")
        return "<HP1>"

    def fake_clear_buffer():
        calls.append("clear_buffer")

    monkeypatch.setattr(connection, "find_prompt", fake_find_prompt)
    monkeypatch.setattr(connection, "clear_buffer", fake_clear_buffer)
    connection.base_prompt = "HP1"

    prompt = connection._prompt_handler(auto_find_prompt=auto_find_prompt)

    expected_prompt = "<HP1>" if auto_find_prompt else "HP1"
    assert prompt == expected_prompt
    if auto_find_prompt:
        assert calls == ["find_prompt", "clear_buffer"]
    else:
        assert calls == []


def test_hp_comware_prompt_handler_clear_buffer_after_find_prompt_fallback(monkeypatch):
    connection = FakeHPComwareConnection()
    calls = []

    def fake_find_prompt():
        calls.append("find_prompt")
        raise ValueError

    def fake_clear_buffer():
        calls.append("clear_buffer")

    monkeypatch.setattr(connection, "find_prompt", fake_find_prompt)
    monkeypatch.setattr(connection, "clear_buffer", fake_clear_buffer)
    connection.base_prompt = "HP1"

    prompt = connection._prompt_handler(auto_find_prompt=True)

    assert prompt == "HP1"
    assert calls == ["find_prompt", "clear_buffer"]
