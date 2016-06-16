from netmiko.ssh_connection import SSHConnection


class AristaSSH(SSHConnection):
    def check_config_mode(self, check_string='(config'):
    	"""Checks if the device is in configuration mode or not."""
        return super(SSHConnection, self).check_config_mode(check_string=check_string)
