from netmiko.ssh_connection import SSHConnection


class EltexSSH(SSHConnection):
    def session_preparation(self):
        """
        Prepare the session after the connection has been established
        """
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.disable_paging(command='terminal datadump')
