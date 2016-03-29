"""Support for Brocade NOS/VDX."""
from netmiko.ssh_connection import SSHConnection


class BrocadeNosSSH(SSHConnection):
    """Support for Brocade NOS/VDX."""
    def enable(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass
