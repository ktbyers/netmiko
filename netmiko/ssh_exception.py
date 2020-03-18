from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException


class NetmikoTimeoutException(SSHException):
    """SSH session timed trying to connect to the device."""

    pass


class NetmikoConnectionException(SSHException):
    """SSH connection failed. Based on Paramiko ssh_exception on intial connection."""

    pass


class NetmikoAuthenticationException(AuthenticationException):
    """SSH authentication exception based on Paramiko AuthenticationException."""

    pass


NetMikoTimeoutException = NetmikoTimeoutException
NetmikoConnectionException = NetmikoConnectionException
NetMikoAuthenticationException = NetmikoAuthenticationException
