#!/usr/bin/env python
"""Regression tests for channel byte-stream decoding (GH #3915).

Channel transports read bytes in chunks whose boundaries do not align with
character boundaries. Decoding each chunk independently with
errors="ignore" silently drops a multi-byte character that is split across
two reads, and the leftover bytes can even be reinterpreted as a different
character. These tests feed scripted byte chunks through fake connections
(no network) and require the decoded output to preserve the original text,
while pinning the read contracts that must not change:

* all available data is drained and returned in order,
* an open connection with no data returns "",
* a closed SSH stream raises ReadException,
* a closed telnet connection with no buffered data raises EOFError.
"""

import pytest

from netmiko._telnetlib import telnetlib
from netmiko.channel import SSHChannel, TelnetChannel, SerialChannel
from netmiko.exceptions import ReadException

# ---------------------------------------------------------------------------
# Fake connections
# ---------------------------------------------------------------------------


class FakeSSHConn:
    """Scripted paramiko.Channel stand-in.

    recv() returns each queued chunk in turn (one chunk per call, ignoring
    the requested size) so tests control exact byte boundaries. A queued
    b"" chunk simulates the remote closing the stream.
    """

    def __init__(self, chunks):
        self.chunks = list(chunks)

    def recv_ready(self):
        return bool(self.chunks)

    def recv(self, n):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def sendall(self, data):
        pass


class FakeSocket:
    """Scripted socket for feeding a real telnetlib.Telnet parser."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = b""

    def recv(self, n):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def sendall(self, data):
        self.sent += data

    def fileno(self):
        return -1

    def close(self):
        pass


class FakeSerial:
    """Scripted serial.Serial stand-in.

    in_waiting reports the size of the next queued chunk; read() returns
    that whole chunk so tests control exact byte boundaries.
    """

    def __init__(self, chunks):
        self.chunks = list(chunks)

    @property
    def in_waiting(self):
        if not self.chunks:
            return 0
        return len(self.chunks[0])

    def read(self, n):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def write(self, data):
        pass

    def flush(self):
        pass


def make_telnet_channel(chunks, encoding="utf-8"):
    """Build a TelnetChannel wrapping a real Telnet fed by a FakeSocket.

    read_eager() loops while `not eof and sock_avail()`; drive the loop off
    the scripted queue instead of a real selector.
    """
    sock = FakeSocket(chunks)
    tn = telnetlib.Telnet()
    tn.sock = sock
    tn.sock_avail = lambda: bool(sock.chunks)  # type: ignore[method-assign]
    return TelnetChannel(conn=tn, encoding=encoding), sock


# ---------------------------------------------------------------------------
# SSHChannel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("split", [1, 2, 3, 4])
def test_ssh_split_gbk_char_within_read_channel(split):
    """A GBK character split across two recv() calls must survive intact.

    This is the GH #3915 failure: the device sends GBK text and a read
    boundary lands inside a two-byte character.
    """
    text = "外联公积金"
    data = text.encode("gbk")
    chan = SSHChannel(conn=FakeSSHConn([data[:split], data[split:]]), encoding="gbk")
    assert chan.read_channel() == text


@pytest.mark.parametrize("split", [1, 2, 3, 4, 5])
def test_ssh_split_utf8_char_within_read_channel(split):
    """A UTF-8 multi-byte character split across two recv() calls survives."""
    text = "中文输出"
    data = text.encode("utf-8")
    chan = SSHChannel(conn=FakeSSHConn([data[:split], data[split:]]), encoding="utf-8")
    assert chan.read_channel() == text


def test_ssh_split_across_read_channel_calls():
    """A character split across two separate read_channel() calls survives.

    read_channel() can legitimately return before the rest of a character
    has arrived; the pending bytes must be held for the next read.
    """
    data = "中文".encode("utf-8")
    conn = FakeSSHConn([data[:2]])
    chan = SSHChannel(conn=conn, encoding="utf-8")
    # First read ends mid-character; only complete characters are returned.
    first = chan.read_channel()
    conn.chunks.append(data[2:])
    assert first + chan.read_channel() == "中文"


def test_ssh_aligned_chunks_unchanged():
    """Control: reads aligned to character boundaries decode as before."""
    data = "router> show version\r\n外联".encode("gbk")
    pieces = [data[:6], data[6:20], data[20:]]
    chan = SSHChannel(conn=FakeSSHConn(pieces), encoding="gbk")
    assert chan.read_channel() == "router> show version\r\n外联"


def test_ssh_no_data_returns_empty():
    """An open connection with nothing to read returns "" (unchanged)."""
    chan = SSHChannel(conn=FakeSSHConn([]), encoding="utf-8")
    assert chan.read_channel() == ""


def test_ssh_closed_stream_still_raises():
    """A closed SSH stream still raises ReadException (unchanged)."""
    chan = SSHChannel(conn=FakeSSHConn([b""]), encoding="utf-8")
    with pytest.raises(ReadException):
        chan.read_channel()


def test_ssh_incomplete_bytes_at_stream_end_not_emitted():
    """Bytes of a character that never completes are not emitted.

    This matches the previous behavior (errors="ignore" dropped them) but
    they are now held in the decoder rather than rewritten to a different
    character.
    """
    data = "中".encode("utf-8")  # three bytes
    chan = SSHChannel(conn=FakeSSHConn([data[:2]]), encoding="utf-8")
    assert chan.read_channel() == ""


# ---------------------------------------------------------------------------
# TelnetChannel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("split", [1, 2, 3, 4, 5])
def test_telnet_split_utf8_char_within_read_channel(split):
    """A UTF-8 character split across socket reads inside one read survives."""
    text = "中文输出"
    data = text.encode("utf-8")
    chan, _sock = make_telnet_channel([data[:split], data[split:]])
    assert chan.read_channel() == text


def test_telnet_split_across_read_channel_calls():
    """A character split across two separate read_channel() calls survives."""
    data = "中文".encode("utf-8")
    chan, sock = make_telnet_channel([data[:2]])
    first = chan.read_channel()
    sock.chunks.append(data[2:])
    assert first + chan.read_channel() == "中文"


def test_telnet_closed_with_no_data_still_raises():
    """A closed telnet connection with no data still raises EOFError.

    telnet_login() relies on this to detect a dropped connection. A single
    empty recv() marks EOF while sock_avail() is initially True.
    """
    chan, _sock = make_telnet_channel([b""])
    with pytest.raises(EOFError):
        chan.read_channel()


# ---------------------------------------------------------------------------
# SerialChannel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("split", [1, 2, 3, 4, 5])
def test_serial_split_utf8_char_across_reads(split):
    """A UTF-8 character split across two serial reads survives."""
    text = "中文输出"
    data = text.encode("utf-8")
    chan = SerialChannel(conn=FakeSerial([data[:split], data[split:]]), encoding="utf-8")
    assert chan.read_channel() == text


def test_serial_no_data_returns_empty():
    """A serial channel with nothing waiting returns "" (unchanged)."""
    chan = SerialChannel(conn=FakeSerial([]), encoding="utf-8")
    assert chan.read_channel() == ""


# ---------------------------------------------------------------------------
# Encoding changes
# ---------------------------------------------------------------------------


def test_encoding_change_recreates_decoder():
    """Changing the channel encoding re-decodes subsequent bytes correctly."""
    chan = SSHChannel(conn=FakeSSHConn(["café".encode("utf-8")]), encoding="utf-8")
    assert chan.read_channel() == "café"
    chan.encoding = "latin-1"
    chan.remote_conn.chunks.append("café".encode("latin-1"))
    assert chan.read_channel() == "café"


# ---------------------------------------------------------------------------
# Decoder lifetime
# ---------------------------------------------------------------------------


def test_decoder_state_isolated_between_instances():
    """Pending bytes on one channel never leak into another channel.

    The decoder attributes have class-level defaults; this verifies that
    assignment creates per-instance state.
    """
    data = "中".encode("utf-8")
    chan_a = SSHChannel(conn=FakeSSHConn([data[:2]]), encoding="utf-8")
    chan_b = SSHChannel(conn=FakeSSHConn(["文".encode("utf-8")]), encoding="utf-8")
    assert chan_a.read_channel() == ""  # partial character held on A
    assert chan_b.read_channel() == "文"  # B is unaffected by A's pending bytes


def test_decoder_resets_when_connection_replaced():
    """Replacing remote_conn must not carry pending bytes into the new stream.

    Netmiko creates a fresh channel object per connection, but the Channel
    class itself must uphold the same guarantee if the underlying connection
    is ever replaced.
    """
    data = "中".encode("utf-8")
    conn = FakeSSHConn([data[:2]])
    chan = SSHChannel(conn=conn, encoding="utf-8")
    assert chan.read_channel() == ""  # two bytes of 中 held in the decoder
    chan.remote_conn = FakeSSHConn(["文".encode("utf-8")])
    assert chan.read_channel() == "文"  # no contamination from the old stream


def test_utf16_split_char_survives():
    """A stateful/BOM encoding split across reads also decodes intact."""
    text = "中文"
    data = text.encode("utf-16")
    # Split inside the BOM+first-character region and inside a code unit.
    chan = SSHChannel(conn=FakeSSHConn([data[:3], data[3:5], data[5:]]), encoding="utf-16")
    assert chan.read_channel() == text
