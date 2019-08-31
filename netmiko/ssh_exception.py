from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException


class NetmikoTimeoutException(SSHException):
    """SSH session timed trying to connect to the device."""

    pass


class NetmikoAuthenticationException(AuthenticationException):
    """SSH authentication exception based on Paramiko AuthenticationException."""

    pass


NetMikoTimeoutException = NetmikoTimeoutException
NetMikoAuthenticationException = NetmikoAuthenticationException
