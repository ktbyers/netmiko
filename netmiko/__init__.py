import logging

# Logging configuration
log = logging.getLogger(__name__)  # noqa
log.addHandler(logging.NullHandler())  # noqa

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

# Alternate naming
Netmiko = ConnectHandler

__version__ = "4.1.0"
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
