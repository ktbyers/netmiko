import sys

__version__ = "4.1.0"
MIN_PYTHON_VER = "3.7"


# Make sure user is using a valid Python version (for Netmiko)
def check_python_version():
    python_snake = "\U0001F40D"

    # Use old-school .format() method in case someone tries to use Netmiko with very old Python
    msg = """

Netmiko Version {net_ver} requires Python Version {py_ver} or higher.

""".format(
        net_ver=__version__, py_ver=MIN_PYTHON_VER
    )
    if sys.version_info.major != 3:
        raise ValueError(msg)
    elif sys.version_info.minor < 7:
        # Why not :-)
        msg = msg.rstrip() + " {snake}\n\n".format(snake=python_snake)
        raise ValueError(msg)


check_python_version()


import logging

from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.ssh_dispatcher import ConnLogOnly
from netmiko.ssh_dispatcher import ConnUnify
from netmiko.ssh_dispatcher import ssh_dispatcher
from netmiko.ssh_dispatcher import redispatch
from netmiko.ssh_dispatcher import platforms
from netmiko.ssh_dispatcher import FileTransfer
from netmiko.scp_handler import SCPConn
from netmiko.cisco.cisco_ios import InLineTransfer
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetMikoTimeoutException,
)
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetMikoAuthenticationException,
)
from netmiko.exceptions import ConfigInvalidException
from netmiko.exceptions import ReadException, ReadTimeout
from netmiko.exceptions import NetmikoBaseException, ConnectionException
from netmiko.ssh_autodetect import SSHDetect
from netmiko.base_connection import BaseConnection
from netmiko.scp_functions import file_transfer, progress_bar

# Logging configuration
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Alternate naming
Netmiko = ConnectHandler

__all__ = (
    "ConnectHandler",
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
