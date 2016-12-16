import logging

from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.ssh_dispatcher import ssh_dispatcher
from netmiko.ssh_dispatcher import platforms
from netmiko.scp_handler import SCPConn
from netmiko.scp_handler import FileTransfer
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException

# Syslog configuration
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Alternate naming
NetmikoTimeoutError = NetMikoTimeoutException
NetmikoAuthError = NetMikoAuthenticationException

__version__ = '1.2.1'

__all__ = ('ConnectHandler', 'ssh_dispatcher', 'platforms', 'SCPConn', 'FileTransfer',
           'NetMikoTimeoutException', 'NetMikoAuthenticationException',
           'NetmikoTimeoutError', 'NetmikoAuthError')

# Test logging
log.critical("Test Message")
