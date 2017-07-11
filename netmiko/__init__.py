from __future__ import unicode_literals
import logging

# Logging configuration
log = logging.getLogger(__name__) # noqa
log.addHandler(logging.NullHandler()) # noqa

from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.ssh_dispatcher import ssh_dispatcher
from netmiko.ssh_dispatcher import redispatch
from netmiko.ssh_dispatcher import platforms
from netmiko.scp_handler import SCPConn
from netmiko.scp_handler import FileTransfer
from netmiko.scp_handler import InLineTransfer
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException
from netmiko.ssh_autodetect import SSHDetect
from netmiko.base_connection import BaseConnection

# Alternate naming
NetmikoTimeoutError = NetMikoTimeoutException
NetmikoAuthError = NetMikoAuthenticationException

__version__ = '1.4.2'

__all__ = ('ConnectHandler', 'ssh_dispatcher', 'platforms', 'SCPConn', 'FileTransfer',
           'NetMikoTimeoutException', 'NetMikoAuthenticationException',
           'NetmikoTimeoutError', 'NetmikoAuthError', 'InLineTransfer', 'redispatch',
           'SSHDetect', 'BaseConnection')

# Cisco cntl-shift-six sequence
CNTL_SHIFT_6 = chr(30)
