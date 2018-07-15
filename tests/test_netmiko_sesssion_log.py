#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import time
import hashlib


def calc_md5(file_name=None, contents=None):
    """Compute MD5 hash of file."""
    if contents is not None:
        pass
    elif file_name:
        with open(file_name, "rb") as f:
            contents = f.read()
    else:
        raise ValueError("Most specify either file_name or contents")

    return hashlib.md5(contents).hexdigest()


def read_session_log(session_file):
    """Leading white-space can vary. Strip off leading white-space."""
    with open(session_file, "rb") as f:
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


def test_session_log(net_connect, commands, expected_responses):
    """Verify session_log matches expected content."""
    command = commands["basic"]
    session_action(net_connect, command)

    compare_file = expected_responses['compare_log']
    session_file = expected_responses['session_log']
    
    session_log_md5(session_file, compare_file)


def test_session_log_write(net_connect_slog_wr, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    command = commands["basic"]
    session_action(net_connect_slog_wr, command)

    compare_file = expected_responses['compare_log_wr']
    session_file = expected_responses['session_log']
    session_log_md5(session_file, compare_file)


def test_session_log_write(net_connect_slog_append, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    command = commands["basic"]
    command_list = [command, command]
    session_action(command)

    compare_file = expected_responses['compare_log_append']
    session_file = expected_responses['session_log_append']
    session_log_md5(session_file, compare_file)
