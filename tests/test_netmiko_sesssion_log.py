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


def test_session_log(net_connect, commands, expected_responses):
    """Verify session_log matches expected content."""
    time.sleep(1)
    net_connect.clear_buffer()
    show_ip_int_br = net_connect.send_command(commands["basic"])

    compare_file = expected_responses['compare_log']
    session_file = expected_responses['session_log']

    net_connect.disconnect()
    compare_log_md5 = calc_md5(file_name=compare_file)
    with open(session_file, "rb") as f:
        log_content = f.read()
        # Leading white-space can vary
        log_content = log_content.lstrip()
        session_log_md5 = calc_md5(contents=log_content)

    assert session_log_md5 == compare_log_md5


def test_session_log_write(net_connect_slog_wr, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    net_connect = net_connect_slog_wr
    time.sleep(1)
    net_connect.clear_buffer()
    show_ip_int_br = net_connect.send_command(commands["basic"])

    compare_file = expected_responses['compare_log_wr']
    session_file = expected_responses['session_log']

    net_connect.disconnect()
    compare_log_md5 = calc_md5(file_name=compare_file)
    with open(session_file, "rb") as f:
        log_content = f.read()
        # Leading white-space can vary
        log_content = log_content.lstrip()
        session_log_md5 = calc_md5(contents=log_content)

    assert session_log_md5 == compare_log_md5
