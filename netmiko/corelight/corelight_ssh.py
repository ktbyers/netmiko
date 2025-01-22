from netmiko.linux.linux_ssh import LinuxSSH
from netmiko.cisco_base_connection import CiscoSSHConnection


class CorelightSSH(LinuxSSH):
    """
    Subclass specific to Corelight.

    This class inherits from LinuxSSH since Corelight's SSH interface is Linux-based.
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Similar to Cisco APIC, we need to handle terminal paging and setup.
        This method customizes the session preparation for Corelight devices.
        """
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        # Disable paging using Cisco's method since it's commonly needed
        CiscoSSHConnection.disable_paging(self, command="terminal length 0")
