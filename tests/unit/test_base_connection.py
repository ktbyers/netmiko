#!/usr/bin/env python

import time
from os.path import dirname, join
from threading import Lock

from netmiko import NetMikoTimeoutException
from netmiko.base_connection import BaseConnection

RESOURCE_FOLDER = join(dirname(dirname(__file__)), "etc")


class FakeBaseConnection(BaseConnection):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._session_locker = Lock()


def test_timeout_exceeded():
    """Raise NetMikoTimeoutException if waiting too much"""
    connection = FakeBaseConnection(session_timeout=10)
    start = time.time() - 11
    try:
        connection._timeout_exceeded(start)
    except NetMikoTimeoutException as exc:
        assert isinstance(exc, NetMikoTimeoutException)
        return

    assert False


def test_timeout_not_exceeded():
    """Do not raise NetMikoTimeoutException if not waiting too much"""
    connection = FakeBaseConnection(session_timeout=10)
    start = time.time()
    assert not connection._timeout_exceeded(start)


def test_timeout_invalid_start():
    """Test invalid timeout start value"""
    connection = FakeBaseConnection(session_timeout=10)
    assert not connection._timeout_exceeded(start=0)


def test_use_ssh_file():
    """Update SSH connection parameters based on the SSH "config" file"""
    connection = FakeBaseConnection(
        host="localhost",
        port=22,
        username="",
        password="secret",
        use_keys=True,
        allow_agent=False,
        key_file="/home/user/.ssh/id_rsa",
        timeout=60,
        pkey=None,
        passphrase=None,
        auth_timeout=None,
        ssh_config_file=join(RESOURCE_FOLDER, "ssh_config"),
    )

    connect_dict = connection._connect_params_dict()

    expected = {
        "hostname": "10.10.10.70",
        "port": 8022,
        "username": "admin",
        "password": "secret",
        "look_for_keys": True,
        "allow_agent": False,
        "key_filename": "/home/user/.ssh/id_rsa",
        "timeout": 60,
        "pkey": None,
        "passphrase": None,
        "auth_timeout": None,
    }

    result = connection._use_ssh_config(connect_dict)
    assert "sock" in result
    assert len(result["sock"].cmd) == 5
    assert "nc" in result["sock"].cmd
    del result["sock"]
    assert result == expected


def test_connect_params_dict():
    """Generate dictionary of Paramiko connection parameters"""
    connection = FakeBaseConnection(
        host="localhost",
        port=22,
        username="user",
        password="secret",
        use_keys=True,
        allow_agent=False,
        key_file="/home/user/.ssh/id_rsa",
        timeout=60,
        pkey=None,
        passphrase=None,
        auth_timeout=None,
        ssh_config_file=None,
    )

    expected = {
        "hostname": "localhost",
        "port": 22,
        "username": "user",
        "password": "secret",
        "look_for_keys": True,
        "allow_agent": False,
        "key_filename": "/home/user/.ssh/id_rsa",
        "timeout": 60,
        "pkey": None,
        "passphrase": None,
        "auth_timeout": None,
    }
    result = connection._connect_params_dict()
    assert result == expected


def test_sanitize_nothing():
    """Keep command echo, trailing router prompt and ANSI escape codes"""

    output = """
show cdp neighbors
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone,
                  D - Remote, C - CVTA, M - Two-port Mac Relay

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID

Total cdp entries displayed : 0
cisco3#"""

    connection = FakeBaseConnection(
        RESPONSE_RETURN="\n",
        RETURN="\n",
        ansi_escape_codes=False,
        base_prompt="cisco3#",
    )

    result = connection._sanitize_output(
        output,
        strip_command=False,
        command_string="show cdp neighbors\n",
        strip_prompt=False,
    )
    assert result == output


def test_sanitize_output():
    """Strip out command echo, trailing router prompt and ANSI escape codes"""

    output = """
show cdp neighbors
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone, 
                  D - Remote, C - CVTA, M - Two-port Mac Relay 

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID

Total cdp entries displayed : 0
cisco3#"""
    output = output.lstrip()

    expected = """
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone, 
                  D - Remote, C - CVTA, M - Two-port Mac Relay 

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID

Total cdp entries displayed : 0"""
    expected = expected.lstrip()

    connection = FakeBaseConnection(
        RESPONSE_RETURN="\n",
        RETURN="\n",
        ansi_escape_codes=False,
        base_prompt="cisco3#",
    )

    result = connection._sanitize_output(
        output,
        strip_command=True,
        command_string="show cdp neighbors\n",
        strip_prompt=True,
    )
    assert result == expected


def test_select_global_delay_factor():
    """Select the global delay factor"""
    connection = FakeBaseConnection(global_delay_factor=4, fast_cli=False)
    assert connection.select_delay_factor(2) == 4


def test_select_current_delay_factor():
    """Select the current delay factor"""
    connection = FakeBaseConnection(global_delay_factor=4, fast_cli=False)
    assert connection.select_delay_factor(10) == 10


def test_strip_prompt():
    """Strip the trailing router prompt from the output"""
    string = """MyRouter version 1.25.9
myhostname>"""
    connection = FakeBaseConnection(RESPONSE_RETURN="\n", base_prompt="myhostname>")
    result = connection.strip_prompt(string)
    assert result == "MyRouter version 1.25.9"


def test_strip_no_prompt():
    """Strip no prompt from the output"""
    string = """MyRouter version 1.25.9
additional text"""
    connection = FakeBaseConnection(RESPONSE_RETURN="\n", base_prompt="myhostname>")
    result = connection.strip_prompt(string)
    assert result == string


def test_strip_no_backspaces():
    """Strip no backspace characters out of the output"""
    text = "Writing something"
    output = BaseConnection.strip_backspaces(text)
    assert output == "Writing something"


def test_strip_one_backspaces():
    """Strip one backspace character out of the output"""
    text = "Writing\x08something"
    output = BaseConnection.strip_backspaces(text)
    assert output == "Writingsomething"


def test_strip_backspaces():
    """Strip any backspace characters out of the output"""
    text = "Writing\x08something\x08"
    output = BaseConnection.strip_backspaces(text)
    assert output == "Writingsomething"


def test_strip_command():
    """Strip command string from output"""

    output = """show cdp neighbors
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone, 
                  D - Remote, C - CVTA, M - Two-port Mac Relay 

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID

Total cdp entries displayed : 0
cisco3#"""

    command = "show cdp neighbors\n"
    expect = """
Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone, 
                  D - Remote, C - CVTA, M - Two-port Mac Relay 

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID

Total cdp entries displayed : 0
cisco3#"""
    expect = expect.lstrip()

    connection = FakeBaseConnection(RESPONSE_RETURN="\n")
    result = connection.strip_command(command, output)
    assert result == expect


def test_strip_command_w_backspaces():
    """Strip command string from output and remove backspaces"""
    output = """echo "hello world"
hello \x08world
myhost\x08name>
"""
    command = 'echo "hello world"'
    expect = """hello world
myhostname>
"""
    connection = FakeBaseConnection(RESPONSE_RETURN="\n")
    result = connection.strip_command(command, output)
    assert result == expect


def test_normalize_linefeeds():
    """Convert combinations of carriage returns and newlines to standardized form."""
    text = """show hostname\r
show version\r\r
show inventory\r\r\r
show interfaces
\r"""
    expected = """show hostname
show version
show inventory
show interfaces
"""
    connection = FakeBaseConnection(RESPONSE_RETURN="\n")
    result = connection.normalize_linefeeds(text)
    assert result == expected


def test_normalize_cmd():
    """Normalize CLI commands to have a single trailing newline"""
    connection = FakeBaseConnection(RETURN="\n")
    result = connection.normalize_cmd("show version \n\n\n ")
    assert result == "show version\n"


def test_unlocking_no_lock():
    """Try unlocking when the lock is already released"""
    connection = FakeBaseConnection()
    assert not connection._session_locker.locked()
    connection._unlock_netmiko_session()
    assert not connection._session_locker.locked()


def test_locking_unlocking():
    """Try to lock and unlock"""
    connection = FakeBaseConnection()
    assert not connection._session_locker.locked()
    connection._lock_netmiko_session()
    assert connection._session_locker.locked()
    connection._unlock_netmiko_session()
    assert not connection._session_locker.locked()


def lock_unlock_timeout(timeout=0):
    """Try to lock when it is already locked"""
    connection = FakeBaseConnection(session_timeout=timeout)
    assert not connection._session_locker.locked()
    connection._lock_netmiko_session()
    assert connection._session_locker.locked()

    try:
        connection._lock_netmiko_session()
    except NetMikoTimeoutException:
        return
    finally:
        assert connection._session_locker.locked()
        connection._unlock_netmiko_session()
        assert not connection._session_locker.locked()

    assert False


def test_lock_timeout():
    """Try to lock when it is already locked"""
    lock_unlock_timeout(0)


def test_lock_timeout_loop():
    """Try to lock when it is already locked, wait 100ms"""
    lock_unlock_timeout(0.2)
