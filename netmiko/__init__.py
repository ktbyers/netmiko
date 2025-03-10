import sys

__version__ = "4.5.0"
PY_MAJ_VER = 3
PY_MIN_VER = 8
MIN_PYTHON_VER = "3.8"


# Make sure user is using a valid Python version (for Netmiko)
def check_python_version():  # type: ignore
    python_snake = "\U0001F40D"

    # Use old-school .format() method in case someone tries to use Netmiko with very old Python
    msg = """

Netmiko Version {net_ver} requires Python Version {py_ver} or higher.

""".format(
        net_ver=__version__, py_ver=MIN_PYTHON_VER
    )
    if sys.version_info.major != PY_MAJ_VER:
        raise ValueError(msg)
    elif sys.version_info.minor < PY_MIN_VER:
        # Why not :-)
        msg = msg.rstrip() + " {snake}\n\n".format(snake=python_snake)
        raise ValueError(msg)


check_python_version()  # type: ignore


import logging  # noqa


# Logging configuration
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


from netmiko.ssh_dispatcher import ConnectHandler  # noqa
from netmiko.ssh_dispatcher import TelnetFallback  # noqa
from netmiko.ssh_dispatcher import ConnLogOnly  # noqa
from netmiko.ssh_dispatcher import ConnUnify  # noqa
from netmiko.ssh_dispatcher import ssh_dispatcher  # noqa
from netmiko.ssh_dispatcher import redispatch  # noqa
from netmiko.ssh_dispatcher import platforms  # noqa
from netmiko.ssh_dispatcher import FileTransfer  # noqa
from netmiko.scp_handler import SCPConn  # noqa
from netmiko.cisco.cisco_ios import InLineTransfer  # noqa
from netmiko.exceptions import (  # noqa
    NetmikoTimeoutException,
    NetMikoTimeoutException,
)
from netmiko.exceptions import (  # noqa
    NetmikoAuthenticationException,
    NetMikoAuthenticationException,
)
from netmiko.exceptions import ConfigInvalidException  # noqa
from netmiko.exceptions import ReadException, ReadTimeout  # noqa
from netmiko.exceptions import NetmikoBaseException, ConnectionException  # noqa
from netmiko.ssh_autodetect import SSHDetect  # noqa
from netmiko.base_connection import BaseConnection  # noqa
from netmiko.scp_functions import file_transfer, progress_bar  # noqa

# Alternate naming
Netmiko = ConnectHandler

__all__ = (
    "ConnectHandler",
    "AgnosticHandler",
    "ConnLogOnly",
    "ConnUnify",
    "ssh_dispatcher",
    "platforms",
    "SCPConn",
    "FileTransfer",
    "NetmikoBaseException",
    "ConnectionException",
    "NetmikoTimeoutException",
    "NetMikoTimeoutException",
    "ConfigInvalidException",
    "ReadException",
    "ReadTimeout",
    "NetmikoAuthenticationException",
    "NetMikoAuthenticationException",
    "InLineTransfer",
    "redispatch",
    "SSHDetect",
    "BaseConnection",
    "Netmiko",
    "file_transfer",
    "progress_bar",
)

# Cisco cntl-shift-six sequence
CNTL_SHIFT_6 = chr(30)
