#!/usr/bin/env python
"""Unit tests for SessionLog that require no network connection.

Layer 1 — Pure SessionLog tests: use io.BytesIO or a temporary file as
the sink; no ConnectHandler involved.

Layer 2 — BaseConnection integration tests: use FakeChannel + FakeConn
to exercise read_channel() / write_channel() without a real SSH session.
"""

import io
import os
import tempfile
from threading import Lock

from netmiko.base_connection import BaseConnection
from netmiko.session_log import SessionLog


# ---------------------------------------------------------------------------
# Layer 2 helpers — FakeChannel and FakeConn
# ---------------------------------------------------------------------------


class FakeChannel:
    """Scripted channel: returns queued strings from read_channel() and
    records everything passed to write_channel()."""

    def __init__(self, responses=()):
        self._responses = list(responses)
        self.writes = []

    def read_channel(self):
        return self._responses.pop(0) if self._responses else ""

    def write_channel(self, data):
        self.writes.append(data)


class FakeConn(BaseConnection):
    """Minimal BaseConnection subclass that skips SSH setup entirely."""

    def __init__(self, slog=None, responses=()):
        self._session_locker = Lock()
        self.disable_lf_normalization = True
        self.ansi_escape_codes = False
        self._read_buffer = ""
        self.encoding = "utf-8"
        self.session_log = slog
        self.channel = FakeChannel(responses)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_slog(no_log=None, record_writes=False):
    """Return a (SessionLog, BytesIO-sink) pair."""
    sink = io.BytesIO()
    slog = SessionLog(buffered_io=sink, no_log=no_log, record_writes=record_writes)
    return slog, sink


def sink_text(sink):
    """Decode BytesIO sink contents as UTF-8."""
    return sink.getvalue().decode("utf-8")


# ---------------------------------------------------------------------------
# Basic write / flush behaviour
# ---------------------------------------------------------------------------


def test_write_flushes_immediately():
    """write() must persist data to the sink without an explicit flush()."""
    slog, sink = make_slog()
    slog.write("hello world")
    assert "hello world" in sink_text(sink)


def test_write_empty_string_is_noop():
    """write('') must not change the sink."""
    slog, sink = make_slog()
    slog.write("")
    assert sink_text(sink) == ""


def test_flush_drains_nothing_when_buffer_empty():
    """flush() on an empty buffer must not raise and must leave sink empty."""
    slog, sink = make_slog()
    slog.flush()
    assert sink_text(sink) == ""


def test_explicit_flush_writes_pending_data():
    """flush() must push any buffered data to the sink."""
    slog, sink = make_slog()
    # Write bypasses the normal flush path by writing directly to slog_buffer
    slog.slog_buffer.write("buffered")
    slog.flush()
    assert "buffered" in sink_text(sink)


def test_multiple_writes_accumulate():
    """Multiple write() calls must all appear in the sink."""
    slog, sink = make_slog()
    slog.write("line1\n")
    slog.write("line2\n")
    slog.write("line3\n")
    result = sink_text(sink)
    assert "line1" in result
    assert "line2" in result
    assert "line3" in result


# ---------------------------------------------------------------------------
# close() behaviour
# ---------------------------------------------------------------------------


def test_close_flushes_remaining_data():
    """close() must flush any data still in slog_buffer."""
    slog, sink = make_slog()
    slog.slog_buffer.write("final")
    slog.close()
    assert "final" in sink_text(sink)


def test_data_present_before_close():
    """Data written via write() must be in the sink before close() is called."""
    slog, sink = make_slog()
    slog.write("early data")
    assert "early data" in sink_text(sink)
    slog.close()
    assert "early data" in sink_text(sink)


# ---------------------------------------------------------------------------
# no_log redaction
# ---------------------------------------------------------------------------


def test_secret_redacted_on_write():
    """A no_log value written via write() must appear as '********' in the sink."""
    secret = "mysecretpassword"
    slog, sink = make_slog(no_log={"password": secret})
    slog.write(f"auth password={secret}\n")
    result = sink_text(sink)
    assert secret not in result
    assert "********" in result


def test_non_secret_data_not_redacted():
    """Normal data must pass through unmodified when no_log is set."""
    slog, sink = make_slog(no_log={"password": "topsecret"})
    slog.write("show version\n")
    assert "show version" in sink_text(sink)


def test_multiple_no_log_entries_all_redacted():
    """Every entry in no_log must be independently redacted."""
    no_log = {
        "user": "admin_username",
        "auth": "snmp_auth_secret",
        "priv": "snmp_priv_secret",
    }
    slog, sink = make_slog(no_log=no_log)
    slog.write("user=admin_username auth=snmp_auth_secret priv=snmp_priv_secret\n")
    result = sink_text(sink)
    for secret in no_log.values():
        assert secret not in result
    assert result.count("********") == 3


def test_secret_not_redacted_when_no_log_empty():
    """With no no_log entries, data must pass through verbatim."""
    slog, sink = make_slog(no_log={})
    slog.write("password=plaintext\n")
    assert "plaintext" in sink_text(sink)


def test_secret_split_across_writes_redacted():
    """A secret split across two write() calls must still be fully redacted."""
    secret = "supersecret"
    slog, sink = make_slog(no_log={"password": secret})
    # Split "supersecret" into "super" + "secret"
    slog.write("super")
    slog.write("secret")
    slog.flush()
    result = sink_text(sink)
    assert secret not in result
    assert "********" in result


# ---------------------------------------------------------------------------
# Partial no_log match at close
# ---------------------------------------------------------------------------


def test_partial_no_log_held_back_on_write():
    """A partial prefix of a secret must not appear unredacted in the sink mid-stream."""
    secret = "supersecret"
    slog, sink = make_slog(no_log={"password": secret})
    slog.write("output ")
    slog.write("superse")  # partial prefix — held back
    # The held-back fragment must not be in the sink yet
    assert "superse" not in sink_text(sink)


def test_partial_no_log_redacted_at_close():
    """A partial prefix held in the buffer at close() must be written as '********'."""
    secret = "supersecret"
    slog, sink = make_slog(no_log={"password": secret})
    slog.write("some output ")
    slog.write("superse")  # partial prefix — held back
    slog.close()
    result = sink_text(sink)
    assert "some output " in result
    assert secret not in result
    assert "********" in result


# ---------------------------------------------------------------------------
# Unicode
# ---------------------------------------------------------------------------


def test_unicode_survives_round_trip():
    """Unicode characters written via write() must appear in the sink."""
    slog, sink = make_slog()
    smiley = "\N{GRINNING FACE WITH SMILING EYES}"
    slog.write(smiley)
    slog.write(smiley)
    result = sink_text(sink)
    assert smiley in result
    assert result.count(smiley) == 2


# ---------------------------------------------------------------------------
# File-based sink (write and append modes)
# ---------------------------------------------------------------------------


def test_file_write_mode():
    """SessionLog opened in write mode must create/overwrite the file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
        fname = f.name
    try:
        slog = SessionLog(file_name=fname, file_mode="write")
        slog.open()
        slog.write("written data\n")
        slog.close()
        with open(fname, "r") as f:
            assert "written data" in f.read()
    finally:
        os.unlink(fname)


def test_file_append_mode_preserves_existing_content():
    """SessionLog in append mode must not overwrite existing file contents."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log", mode="w") as f:
        fname = f.name
        f.write("Initial file contents\n")
    try:
        slog = SessionLog(file_name=fname, file_mode="append")
        slog.open()
        slog.write("appended data\n")
        slog.close()
        with open(fname, "r") as f:
            contents = f.read()
        assert "Initial file contents" in contents
        assert "appended data" in contents
    finally:
        os.unlink(fname)


def test_file_write_mode_redacts_secret():
    """Secrets must be redacted when the sink is a real file."""
    secret = "filepassword"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
        fname = f.name
    try:
        slog = SessionLog(file_name=fname, file_mode="write", no_log={"password": secret})
        slog.open()
        slog.write(f"auth={secret}\n")
        slog.close()
        with open(fname, "r") as f:
            contents = f.read()
        assert secret not in contents
        assert "********" in contents
    finally:
        os.unlink(fname)


# ---------------------------------------------------------------------------
# Layer 2 — BaseConnection integration (FakeConn + FakeChannel)
# ---------------------------------------------------------------------------


def test_read_channel_logged():
    """Data returned by the channel's read_channel() must appear in the session log."""
    slog, sink = make_slog()
    conn = FakeConn(slog=slog, responses=["router# show version\n"])
    conn.read_channel()
    assert "show version" in sink_text(sink)


def test_read_channel_empty_response_not_logged():
    """An empty read from the channel must not write anything to the session log."""
    slog, sink = make_slog()
    conn = FakeConn(slog=slog, responses=[""])
    conn.read_channel()
    assert sink_text(sink) == ""


def test_multiple_read_channel_calls_all_logged():
    """Every read_channel() call must append its data to the session log."""
    slog, sink = make_slog()
    conn = FakeConn(slog=slog, responses=["first\n", "second\n", "third\n"])
    conn.read_channel()
    conn.read_channel()
    conn.read_channel()
    result = sink_text(sink)
    assert "first" in result
    assert "second" in result
    assert "third" in result


def test_write_channel_not_logged_by_default():
    """write_channel() must not log to the session log when record_writes=False."""
    slog, sink = make_slog(record_writes=False)
    conn = FakeConn(slog=slog)
    conn.write_channel("show interfaces\n")
    assert sink_text(sink) == ""


def test_write_channel_logged_when_record_writes():
    """write_channel() must log to the session log when record_writes=True."""
    slog, sink = make_slog(record_writes=True)
    conn = FakeConn(slog=slog)
    conn.write_channel("show interfaces\n")
    assert "show interfaces" in sink_text(sink)


def test_read_channel_no_log_redacted():
    """A no_log secret arriving via read_channel() must be redacted in the session log."""
    secret = "topsecret"
    slog, sink = make_slog(no_log={"password": secret})
    conn = FakeConn(slog=slog, responses=[f"auth {secret}\n"])
    conn.read_channel()
    result = sink_text(sink)
    assert secret not in result
    assert "********" in result


def test_write_channel_no_log_redacted_with_record_writes():
    """A no_log secret sent via write_channel() must be redacted when record_writes=True."""
    secret = "topsecret"
    slog, sink = make_slog(no_log={"password": secret}, record_writes=True)
    conn = FakeConn(slog=slog)
    conn.write_channel(f"{secret}\n")
    result = sink_text(sink)
    assert secret not in result
    assert "********" in result


def test_no_session_log_does_not_raise():
    """read_channel() and write_channel() must work fine when session_log is None."""
    conn = FakeConn(slog=None, responses=["some output\n"])
    output = conn.read_channel()
    conn.write_channel("cmd\n")
    assert output == "some output\n"
