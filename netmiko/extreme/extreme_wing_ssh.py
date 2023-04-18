from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeWingSSH(CiscoSSHConnection):
    """Extreme WiNG support."""

    def session_preparation(self) -> None:
        """Disable paging and set Max term width"""
        self._test_channel_read(pattern=r">|#")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512", pattern="terminal")
        self.disable_paging(command="no page")
