import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeFastironSSH(CiscoSSHConnection):
    """Brocade FastIron aka ICX support."""
    def session_preparation(self):
        """FastIron requires to be enable mode to disable paging."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n\r\n', '\r\r\n','\r\n', '\n\r' to '\n."""
        newline = re.compile(r'(\r\n\r\n|\r\r\n|\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)
