from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.ssh_dispatcher import ssh_dispatcher
from netmiko.ssh_dispatcher import platforms
from netmiko.scp_handler import SCPConn
from netmiko.scp_handler import FileTransfer
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException

# Alternate naming
NetmikoTimeoutError = NetMikoTimeoutException
NetmikoAuthError = NetMikoAuthenticationException

__version__ = '1.1.0'

__all__ = ('ConnectHandler', 'ssh_dispatcher', 'platforms', 'SCPConn', 'FileTransfer',
           'NetMikoTimeoutException', 'NetMikoAuthenticationException',
           'NetmikoTimeoutError', 'NetmikoAuthError')
