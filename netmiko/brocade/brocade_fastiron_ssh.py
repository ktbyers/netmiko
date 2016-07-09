from netmiko.ssh_connection import SSHConnection


class BrocadeFastironSSH(SSHConnection):
    """Brocade FastIron aka ICX support."""
    def session_preparation(self):
        """FastIron requires to be enable mode to disable paging."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")
