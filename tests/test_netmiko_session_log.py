#!/usr/bin/env python
import time
import hashlib
import io
from netmiko import ConnectHandler


def calc_md5(file_name=None, contents=None):
    """Compute MD5 hash of file."""
    if contents is not None:
        pass
    elif file_name:
        with open(file_name, "rb") as f:
            contents = f.read()
    else:
        raise ValueError("Most specify either file_name or contents")

    return hashlib.md5(contents.strip()).hexdigest()


def read_session_log(session_file, append=False):
    """Leading white-space can vary. Strip off leading white-space."""
    with open(session_file, "rb") as f:
        if append is True:
            line = f.readline().decode()
            assert "Initial file contents" in line
        log_content = f.read().lstrip()
        return log_content


def session_action(my_connect, command):
    """Common actions in the netmiko session to generate the session log."""
    time.sleep(1)
    my_connect.clear_buffer()
    output = my_connect.send_command(command)
    my_connect.disconnect()
    return output


def session_log_md5(session_file, compare_file):
    """Compare the session_log MD5 to the compare_file MD5"""
    compare_log_md5 = calc_md5(file_name=compare_file)
    log_content = read_session_log(session_file)
    session_log_md5 = calc_md5(contents=log_content)
    assert session_log_md5 == compare_log_md5


def session_log_md5_append(session_file, compare_file):
    """Compare the session_log MD5 to the compare_file MD5"""
    compare_log_md5 = calc_md5(file_name=compare_file)
    log_content = read_session_log(session_file, append=True)
    session_log_md5 = calc_md5(contents=log_content)
    assert session_log_md5 == compare_log_md5


def test_session_log(net_connect, commands, expected_responses):
    """Verify session_log matches expected content."""
    command = commands["basic"]
    session_action(net_connect, command)

    compare_file = expected_responses["compare_log"]
    session_file = expected_responses["session_log"]

    session_log_md5(session_file, compare_file)


def test_session_log_write(net_connect_slog_wr, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    command = commands["basic"]
    session_action(net_connect_slog_wr, command)

    compare_file = expected_responses["compare_log_wr"]
    session_file = expected_responses["session_log_wr"]
    session_log_md5(session_file, compare_file)


def test_session_log_append(device_slog, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    session_file = expected_responses["session_log_append"]
    # Create a starting file
    with open(session_file, "wb") as f:
        f.write(b"Initial file contents\n\n")

    # The netmiko connection has not been established yet.
    device_slog["session_log"] = session_file

    conn = ConnectHandler(**device_slog)
    command = commands["basic"]
    session_action(conn, command)

    compare_file = expected_responses["compare_log_append"]
    session_log_md5_append(session_file, compare_file)


def test_session_log_bytesio(device_slog, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    s_log = io.BytesIO()

    # The netmiko connection has not been established yet.
    device_slog["session_log"] = s_log
    device_slog["session_log_file_mode"] = "write"

    conn = ConnectHandler(**device_slog)
    command = commands["basic"]
    session_action(conn, command)

    compare_file = expected_responses["compare_log"]
    compare_log_md5 = calc_md5(file_name=compare_file)

    log_content = s_log.getvalue()
    session_log_md5 = calc_md5(contents=log_content)
    assert session_log_md5 == compare_log_md5


def test_session_log_secrets(device_slog):
    """Verify session_log does not contain password or secret."""
    conn = ConnectHandler(**device_slog)
    conn._write_session_log("\nTesting password and secret replacement\n")
    conn._write_session_log("This is my password {}\n".format(conn.password))
    conn._write_session_log("This is my secret {}\n".format(conn.secret))

    if not isinstance(conn.session_log, io.BufferedIOBase):
        with open(conn.session_log.name, "r") as f:
            session_log = f.read()
        if conn.password:
            assert conn.password not in session_log
        if conn.secret:
            assert conn.secret not in session_log
    else:
        assert True
