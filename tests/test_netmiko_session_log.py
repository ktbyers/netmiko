#!/usr/bin/env python
import time
import hashlib
import io
import logging
from netmiko import ConnectHandler
from netmiko.session_log import SessionLog


def add_test_name_to_file_name(initial_fname, test_name):
    dir_name, f_name = initial_fname.split("/")
    new_file_name = f"{dir_name}/{test_name}-{f_name}"
    return new_file_name


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
    nc = net_connect_slog_wr

    # Send a marker down the channel
    nc.send_command("show foooooooo")
    time.sleep(1)
    nc.clear_buffer()
    nc.send_command(command)
    nc.disconnect()

    compare_file = expected_responses["compare_log_wr"]
    session_file = expected_responses["session_log_wr"]

    with open(compare_file, "rb") as f:
        compare_contents = f.read()

    # Header information varies too much due to device behavior differences.
    # So just discard it.
    marker = b"% Invalid input detected at '^' marker."
    _, compare_contents = compare_contents.split(marker)
    compare_log_md5 = calc_md5(contents=compare_contents.strip())

    log_content = read_session_log(session_file)
    marker = b"% Invalid input detected at '^' marker."
    _, log_content = log_content.split(marker)

    session_log_md5 = calc_md5(contents=log_content.strip())
    assert session_log_md5 == compare_log_md5


def test_session_log_append(device_slog_test_name, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""

    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = expected_responses["session_log_append"]
    session_file = add_test_name_to_file_name(slog_file, test_name)

    # Create a starting file
    with open(session_file, "wb") as f:
        f.write(b"Initial file contents\n\n")

    # The netmiko connection has not been established yet.
    device_slog["session_log"] = session_file
    device_slog["session_log_file_mode"] = "append"

    conn = ConnectHandler(**device_slog)
    command = commands["basic"]
    session_action(conn, command)

    compare_file_base = expected_responses["compare_log_append"]
    dir_name, f_name = compare_file_base.split("/")
    compare_file = f"{dir_name}/{test_name}-{f_name}"
    session_log_md5_append(session_file, compare_file)


def test_session_log_secrets(device_slog_test_name):
    """Verify session_log does not contain password or secret."""
    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = device_slog["session_log"]

    new_slog_file = add_test_name_to_file_name(slog_file, test_name)
    device_slog["session_log"] = new_slog_file

    conn = ConnectHandler(**device_slog)
    conn.session_log.write("\nTesting password and secret replacement\n")
    conn.session_log.write("This is my password {}\n".format(conn.password))
    conn.session_log.write("This is my secret {}\n".format(conn.secret))
    time.sleep(1)
    conn.session_log.flush()
    conn.disconnect()

    file_name = device_slog["session_log"]
    with open(file_name, "r") as f:
        session_log = f.read()
    if conn.password:
        assert conn.password not in session_log
    if conn.secret:
        assert conn.secret not in session_log
    assert "terminal width" in session_log


def test_logging_filter_secrets(device_slog_test_name):
    """Verify logging DEBUG output does not contain password or secret."""

    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]

    # No session_log for this test
    del device_slog["session_log"]

    # Set the secret to be correct
    device_slog["secret"] = device_slog["password"]

    nc = ConnectHandler(**device_slog)

    # setup logger to output to file
    file_name = f"SLOG/{test_name}-netmiko.log"
    netmikologger = logging.getLogger("netmiko")
    netmikologger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(logging.DEBUG)
    netmikologger.addHandler(file_handler)

    # cleanup the log file
    with open(file_name, "w") as f:
        f.write("")

    # run sequence
    nc.enable()
    time.sleep(1)
    nc.clear_buffer()
    nc.disconnect()

    with open(file_name, "r") as f:
        netmiko_log = f.read()
    if nc.password:
        assert nc.password not in netmiko_log
    if nc.secret:
        assert nc.secret not in netmiko_log


def test_unicode(device_slog_test_name):
    """Verify that you can write unicode characters into the session_log."""
    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = device_slog["session_log"]

    new_slog_file = add_test_name_to_file_name(slog_file, test_name)
    device_slog["session_log"] = new_slog_file

    conn = ConnectHandler(**device_slog)

    smiley_face = "\N{grinning face with smiling eyes}"
    conn.session_log.write("\nTesting unicode\n")
    conn.session_log.write(smiley_face)
    conn.session_log.write(smiley_face)

    conn.disconnect()

    file_name = device_slog["session_log"]
    with open(file_name, "r") as f:
        session_log = f.read()
        assert smiley_face in session_log


def test_session_log_bytesio(device_slog_test_name, commands, expected_responses):
    """Verify session_log matches expected content, but when channel writes are also logged."""
    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]

    s_log = io.BytesIO()

    # The netmiko connection has not been established yet.
    device_slog["session_log"] = s_log
    device_slog["session_log_file_mode"] = "write"
    device_slog["session_log_record_writes"] = True

    conn = ConnectHandler(**device_slog)
    command = commands["basic"]
    session_action(conn, command)
    conn.disconnect()

    compare_file = expected_responses["compare_log"]
    compare_file = add_test_name_to_file_name(compare_file, test_name)
    compare_log_md5 = calc_md5(file_name=compare_file)

    log_content = s_log.getvalue()
    session_log_md5 = calc_md5(contents=log_content)
    assert session_log_md5 == compare_log_md5


def test_session_log_no_log(device_slog_test_name):
    """Test no_log works properly for show commands."""

    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = device_slog["session_log"]
    new_slog_file = add_test_name_to_file_name(slog_file, test_name)

    # record_writes as well to make sure both the write and read-echo don't get logged.
    device_slog["session_log"] = new_slog_file
    device_slog["session_log_record_writes"] = True

    conn = ConnectHandler(**device_slog)

    # After connection change the password to "invalid"
    fake_password = "invalid"
    conn.password = fake_password

    # Now try to actually send the fake password as a show command
    conn.send_command(fake_password)
    time.sleep(1)
    conn.send_command_timing(fake_password)

    with open(new_slog_file, "r") as f:
        session_log = f.read()

    assert fake_password not in session_log
    # One for read, one for write, one for Cisco "translating" (send_command)
    # Plus one for read, one for write (send_command_timing)
    assert session_log.count("********") == 5

    # Do disconnect after test (to make sure send_command() actually flushes session_log buffer)
    conn.disconnect()


def test_session_log_no_log_cfg(device_slog_test_name, commands):
    """Test no_log works properly for config commands."""
    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = device_slog["session_log"]
    new_slog_file = add_test_name_to_file_name(slog_file, test_name)

    # Likely "logging buffered 20000" (hide/obscure this command)
    config_command1 = commands["config"][0]

    # Likely "no logging console" (this command should show up in the log)
    config_command2 = commands["config"][1]

    # Dict of strings that should be sanitized
    no_log = {
        "cfg1": config_command1,
    }
    # Create custom session log (use 'record_writes' just to test that situation)
    custom_log = SessionLog(file_name=new_slog_file, no_log=no_log, record_writes=True)

    # Pass in custom SessionLog obj to session_log attribute
    device_slog["session_log"] = custom_log
    device_slog["secret"] = device_slog["password"]

    conn = ConnectHandler(**device_slog)
    conn.enable()
    conn.send_config_set([config_command1, config_command2])

    # Check the results
    with open(new_slog_file, "r") as f:
        session_log = f.read()

    assert config_command1 not in session_log
    assert session_log.count("********") == 2
    assert config_command2 in session_log

    # Make sure send_config_set flushes the session_log (so disconnect after the asserts)
    conn.disconnect()


def test_session_log_custom_session_log(device_slog_test_name):
    """Verify session_log does not contain custom words (use SessionLog obj)."""
    device_slog = device_slog_test_name[0]
    test_name = device_slog_test_name[1]
    slog_file = device_slog["session_log"]
    new_slog_file = add_test_name_to_file_name(slog_file, test_name)

    # Dict of words that should be sanitized in session log
    sanitize_secrets = {
        "secret1": "admin_username",
        "secret2": "snmp_auth_secret",
        "secret3": "snmp_priv_secret",
        "supersecret": "supersecret",
        "data1": "terminal length 0",  # Hide something that Netmiko sends
    }
    # Create custom session log
    custom_log = SessionLog(file_name=new_slog_file, no_log=sanitize_secrets)

    # Pass in custom SessionLog obj to session_log attribute
    device_slog["session_log"] = custom_log

    conn = ConnectHandler(**device_slog)
    conn.session_log.write("\nTesting password and secret replacement\n")
    conn.session_log.write(
        "This is my first secret {}\n".format(sanitize_secrets["secret1"])
    )
    conn.session_log.write(
        "This is my second secret {}\n".format(sanitize_secrets["secret2"])
    )
    conn.session_log.write(
        "This is my third secret {}\n".format(sanitize_secrets["secret3"])
    )
    conn.session_log.write(
        "This is my super secret {}\n".format(sanitize_secrets["supersecret"])
    )
    time.sleep(1)
    conn.session_log.flush()

    # Use send_command and send_command_timing to send something that should be filtered
    conn.session_log.write(
        "\n!Testing send_command() and send_command_timing() filtering"
    )
    conn.send_command(sanitize_secrets["data1"])
    conn.send_command_timing(sanitize_secrets["data1"])

    # Retrieve the file name.
    file_name = custom_log.file_name
    with open(file_name, "r") as f:
        session_log = f.read()

    # Ensure file exists and has logging content
    assert "terminal width" in session_log

    # 'terminal length 0' should be hidden in the session_log
    assert "terminal length" not in session_log
    assert ">********" in session_log

    if sanitize_secrets.get("secret1") is not None:
        assert sanitize_secrets["secret1"] not in session_log
    if sanitize_secrets.get("secret2") is not None:
        assert sanitize_secrets["secret2"] not in session_log
    if sanitize_secrets.get("secret3") is not None:
        assert sanitize_secrets["secret3"] not in session_log
    if sanitize_secrets.get("supersecret") is not None:
        assert sanitize_secrets["supersecret"] not in session_log
