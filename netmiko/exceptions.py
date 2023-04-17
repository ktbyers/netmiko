from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException


class NetmikoBaseException(Exception):
    """General base exception except for exceptions that inherit from Paramiko."""

    pass


class ConnectionException(NetmikoBaseException):
    """Generic exception indicating the connection failed."""

    pass


class NetmikoTimeoutException(SSHException):
    """SSH session timed trying to connect to the device."""

    pass


NetMikoTimeoutException = NetmikoTimeoutException


class NetmikoAuthenticationException(AuthenticationException):
    """SSH authentication exception based on Paramiko AuthenticationException."""

    pass


NetMikoAuthenticationException = NetmikoAuthenticationException


class ConfigInvalidException(NetmikoBaseException):
    """Exception raised for invalid configuration error."""

    pass


class WriteException(NetmikoBaseException):
    """General exception indicating an error occurred during a Netmiko write operation."""

    pass


class ReadException(NetmikoBaseException):
    """General exception indicating an error occurred during a Netmiko read operation."""

    pass


class ReadTimeout(ReadException):
    """General exception indicating an error occurred during a Netmiko read operation."""

    pass
