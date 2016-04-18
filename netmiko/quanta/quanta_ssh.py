from netmiko.ssh_connection import SSHConnection


class QuantaSSH(SSHConnection):
    def disable_paging(self, command="no pager", delay_factor=.1):
        """Disable paging"""
        return super(QuantaSSH, self).disable_paging(command=command)

    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(QuantaSSH, self).config_mode(config_command=config_command)
