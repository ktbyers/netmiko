
from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import AuthenticationException


class NetMikoTimeoutException(SSHException):
    '''
    SSH session timed trying to connect to the device

    Based on Paramiko SSHException
    '''
    pass


class NetMikoAuthenticationException(AuthenticationException):
    '''
    SSH authentication exception based on Paramiko AuthenticationException
    '''
    pass
