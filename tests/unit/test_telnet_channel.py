#!/usr/bin/env python
"""Characterization ("before") tests for TelnetChannel.read_channel().

These tests pin down the *current* behavior of reading from a telnet channel,
which is driven by the vendored telnetlib's ``read_very_eager()``. They require
no network connection: a fake socket feeds scripted byte chunks into a real
``telnetlib.Telnet`` parser, and ``sock_avail()`` is stubbed to report whether
more scripted data remains.

The point of these tests is to document the contract that any performance fix
for the O(n^2) ``read_very_eager()`` behavior must preserve exactly:

* all immediately-available data is drained and returned in order,
* IAC/telnet-option bytes are stripped and the correct response is sent,
* an IAC sequence split across recv() boundaries still parses correctly,
* a closed-with-no-data connection raises EOFError (relied on by telnet_login),
* an open connection with no data returns "".
"""

import pytest

from netmiko._telnetlib import telnetlib
from netmiko.channel import TelnetChannel


# ---------------------------------------------------------------------------
# Fake socket + channel builder
# ---------------------------------------------------------------------------


class FakeSocket:
    """Scripted socket.

    ``recv()`` returns each queued chunk in turn (one chunk per call,
    ignoring the requested size so tests can control exact byte boundaries).
    An empty ``b""`` chunk simulates the remote closing the connection.
    ``sendall()`` records bytes written back (telnet option responses).
    """

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = b""

    def recv(self, n):
        if not self.chunks:
            return b""  # EOF
        return self.chunks.pop(0)

    def sendall(self, data):
        self.sent += data

    def fileno(self):
        return -1

    def close(self):
        pass


def make_channel(chunks, encoding="utf-8"):
    """Build a TelnetChannel wrapping a real Telnet fed by a FakeSocket."""
    tn = telnetlib.Telnet()
    fake = FakeSocket(chunks)
    tn.sock = fake
    # read_very_eager() loops while `not eof and sock_avail()`. Drive the loop
    # off the scripted queue instead of a real selector.
    tn.sock_avail = lambda: bool(fake.chunks)  # type: ignore[method-assign]
    channel = TelnetChannel(conn=tn, encoding=encoding)
    return channel, tn, fake


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IAC = telnetlib.IAC
DO = telnetlib.DO
DONT = telnetlib.DONT
WILL = telnetlib.WILL
WONT = telnetlib.WONT
ECHO = telnetlib.ECHO


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_multi_chunk_is_fully_drained_in_order():
    """All immediately-available chunks are returned, concatenated in order."""
    chunks = [b"line1\n", b"line2\n", b"line3\n"]
    channel, _tn, _fake = make_channel(chunks)
    assert channel.read_channel() == "line1\nline2\nline3\n"


def test_iac_option_is_stripped_and_answered():
    """IAC WILL <opt> is removed from cooked output and answered with DONT."""
    chunks = [b"AB" + IAC + WILL + ECHO + b"CD"]
    channel, _tn, fake = make_channel(chunks)
    output = channel.read_channel()
    assert output == "ABCD"
    # Default (no option_callback) telnetlib refuses the option.
    assert fake.sent == IAC + DONT + ECHO


def test_iac_do_is_answered_with_wont():
    """IAC DO <opt> is removed and answered with WONT."""
    chunks = [IAC + DO + ECHO + b"hello"]
    channel, _tn, fake = make_channel(chunks)
    output = channel.read_channel()
    assert output == "hello"
    assert fake.sent == IAC + WONT + ECHO


def test_iac_sequence_split_across_recv_boundaries():
    """An IAC sequence spanning two recv() chunks still parses correctly."""
    # IAC starts at the end of chunk 1, command/option arrive in chunk 2.
    chunks = [b"AB" + IAC, WILL + ECHO + b"CD"]
    channel, _tn, fake = make_channel(chunks)
    output = channel.read_channel()
    assert output == "ABCD"
    assert fake.sent == IAC + DONT + ECHO


def test_closed_connection_with_no_data_raises_eoferror():
    """A closed connection with no cooked data raises EOFError.

    telnet_login() relies on this to detect a dropped/refused login and
    convert it into a NetmikoAuthenticationException.
    """
    # A single empty recv() marks EOF while sock_avail() is initially True.
    channel, _tn, _fake = make_channel([b""])
    with pytest.raises(EOFError):
        channel.read_channel()


def test_no_data_but_open_returns_empty_string():
    """No data available and connection still open returns ''."""
    channel, _tn, _fake = make_channel([])
    assert channel.read_channel() == ""


def test_data_then_close_returns_data_without_raising():
    """When data and EOF arrive together, the data is returned (no raise).

    EOFError is only raised on the *next* read, once the buffer is empty.
    """
    channel, _tn, _fake = make_channel([b"final output\n", b""])
    assert channel.read_channel() == "final output\n"
    # Buffer now empty and connection closed -> next read raises.
    with pytest.raises(EOFError):
        channel.read_channel()


def test_large_input_is_returned_correctly():
    """A large multi-chunk read returns byte-for-byte correct output."""
    chunks = [f"row{i:06d},value{i}\n".encode() for i in range(5000)]
    expected = "".join(c.decode() for c in chunks)
    channel, _tn, _fake = make_channel(chunks)
    assert channel.read_channel() == expected
