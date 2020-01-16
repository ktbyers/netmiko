#!/usr/bin/env python

import time
from os.path import dirname, join
from threading import Lock

from netmiko import NetmikoTimeoutException
from netmiko.base_connection import BaseConnection

RESOURCE_FOLDER = join(dirname(dirname(__file__)), "etc")


class FakeBaseConnection(BaseConnection):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._session_locker = Lock()


def test_timeout_exceeded():
    """Raise NetmikoTimeoutException if waiting too much"""
    connection = FakeBaseConnection(session_timeout=10)
    start = time.time() - 11
    try:
        connection._timeout_exceeded(start)
    except NetmikoTimeoutException as exc:
        assert isinstance(exc, NetmikoTimeoutException)
        return

    assert False


def test_timeout_not_exceeded():
    """Do not raise NetmikoTimeoutException if not waiting too much"""
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
        banner_timeout=10,
        ssh_config_file=join(RESOURCE_FOLDER, "ssh_config"),
        sock=None,
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
        "banner_timeout": 10,
    }

    result = connection._use_ssh_config(connect_dict)
    assert "sock" in result
    assert len(result["sock"].cmd) == 5
    assert "nc" in result["sock"].cmd
    del result["sock"]
    assert result == expected


def test_use_ssh_file_proxyjump():
    """Update SSH connection parameters based on the SSH "config" file"""
    connection = FakeBaseConnection(
        host="10.10.10.70",
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
        banner_timeout=10,
        ssh_config_file=join(RESOURCE_FOLDER, "ssh_config_proxyjump"),
        sock=None,
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
        "banner_timeout": 10,
    }

    result = connection._use_ssh_config(connect_dict)
    assert "sock" in result
    assert "-W" in result["sock"].cmd
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
        banner_timeout=10,
        ssh_config_file=None,
        sock=None,
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
        "banner_timeout": 10,
        "sock": None,
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
    except NetmikoTimeoutException:
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


def test_strip_ansi_codes():
    connection = FakeBaseConnection(RETURN="\n")
    ansi_codes_to_strip = [
        "\x1b[30m",  # Black
        "\x1b[31m",  # Red
        "\x1b[32m",  # Green
        "\x1b[33m",  # Yellow
        "\x1b[34m",  # Blue
        "\x1b[35m",  # Magenta
        "\x1b[36m",  # Cyan
        "\x1b[37m",  # White
        "\x1b[39m",  # Default(foreground color at startup)
        "\x1b[90m",  # Light Gray
        "\x1b[91m",  # Light Red
        "\x1b[92m",  # Light Green
        "\x1b[93m",  # Light Yellow
        "\x1b[94m",  # Light Blue
        "\x1b[95m",  # Light Magenta
        "\x1b[96m",  # Light Cyan
        "\x1b[97m",  # Light White
        "\x1b[40m",  # Black
        "\x1b[41m",  # Red
        "\x1b[42m",  # Green
        "\x1b[43m",  # Yellow
        "\x1b[44m",  # Blue
        "\x1b[45m",  # Magenta
        "\x1b[46m",  # Cyan
        "\x1b[47m",  # White
        "\x1b[49m",  # Default(background color at startup)
        "\x1b[100m",  # Light Gray
        "\x1b[101m",  # Light Red
        "\x1b[102m",  # Light Green
        "\x1b[103m",  # Light Yellow
        "\x1b[104m",  # Light Blue
        "\x1b[105m",  # Light Magenta
        "\x1b[106m",  # Light Cyan
        "\x1b[107m",  # Light White
        "\x1b[1;5H",  # code_position_cursor r"\[\d+;\d+H"
        "\x1b[?25h",  # code_show_cursor
        "\x1b[K",  # code_erase_line_end
        "\x1b[2K",  # code_erase_line
        "\x1b[K",  # code_erase_start_line
        "\x1b[1;2r",  # code_enable_scroll
        "\x1b[1L",  # code_form_feed
        "\x1b[1M",  # code_carriage_return
        "\x1b[?7l",  # code_disable_line_wrapping
        "\x1b[?7l",  # code_reset_mode_screen_options
        "\x1b[00m",  # code_reset_graphics_mode
        "\x1b[J",  # code_erase_display
        "\x1b[6n",  # code_get_cursor_position
        "\x1b[m",  # code_cursor_position
        "\x1b[J",  # code_erase_display
        "\x1b[0m",  # code_attrs_off
        "\x1b[7m",  # code_reverse
    ]
    for ansi_code in ansi_codes_to_strip:
        assert connection.strip_ansi_escape_codes(ansi_code) == ""

    # code_next_line must be substituted with a return
    assert connection.strip_ansi_escape_codes("\x1bE") == "\n"
