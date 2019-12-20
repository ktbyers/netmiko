from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException


class NetmikoTimeoutException(SSHException):
    """SSH session timed trying to connect to the device."""

    def __init__(self, *args):
        super().__init__(args[0])
        if len(args) > 1:
            self.output = args[1]


class NetmikoAuthenticationException(AuthenticationException):
    """SSH authentication exception based on Paramiko AuthenticationException."""

    pass


NetMikoTimeoutException = NetmikoTimeoutException
NetMikoAuthenticationException = NetmikoAuthenticationException
