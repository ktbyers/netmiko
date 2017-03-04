"""
This module is used to auto-detect the type of a device in order to automatically create a
Netmiko connection.

The will avoid to hard coding the 'device_type' when using the ConnectHandler factory function
from Netmiko.
"""

from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE, ConnectHandler

SSH_MAPPER_BASE = {}
for k, v in CLASS_MAPPER_BASE.items():
    if getattr(v, "autodetect", None):
        SSH_MAPPER_BASE[k] = v


class SSHDetect(object):
    """
    The SSHDetect class tries to automatically guess the device type running on the SSH remote end.

    Parameters
    ----------
    *args : list
        The same *args that you might provide to the netmiko.ssh_dispatcher.ConnectHandler.
    *kwargs : dict
        The same *kwargs that you might provide to the netmiko.ssh_dispatcher.ConnectHandler.

    Attributes
    ----------
    connection : netmiko.terminal_server.TerminalServer
        A basic connection to the remote SSH end.
    potential_matches: dict
        Dict of (device type, accuracy) that is populated trough a interaction with the remote end.

    Methods
    -------
    autodetect()
        Try to determine the device type.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the SSHDetect class
        """
        self.connection = ConnectHandler(*args, **kwargs)
        if self.connection.device_type != "terminal_server":
            self.connection.disconnect()
            raise ValueError("The connection device_type must be of 'terminal_server'")

        self.potential_matches = {}

    def autodetect(self):
        """
        Try to guess the best 'device_type' based on each device_type autodetect method.

        Returns
        -------
        bast_match : str or None
            The device type that is currently the best to use to interact with the device
        """
        for k, v in SSH_MAPPER_BASE.items():
            try:
                accuracy = v._autodetect(self.connection)
                self.potential_matches[k] = accuracy
            except Exception:
                pass

        if not self.potential_matches:
            self.connection.disconnect()
            return None

        best_match = sorted(self.potential_matches.items(), key=lambda t: t[1], reverse=True)
        self.connection.disconnect()
        return best_match[0][0]
