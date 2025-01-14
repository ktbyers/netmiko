"""Subclass specific to Cisco APIC."""

from netmiko.linux.linux_ssh import LinuxSSH
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoApicSSH(LinuxSSH):
    """
    Subclass specific to Cisco APIC.

    This class inherit from LinuxSSH because Cisco APIC is based on Linux
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        In LinuxSSH, the disable_paging method does nothing; however, paging is enabled
        by default on Cisco APIC. To handle this, we utilize the disable_paging method
        from CiscoSSHConnection, the parent class of LinuxSSH. This approach leverages
        the shared implementation for Cisco SSH connections and ensures that any updates to
        disable_paging in the parent class are inherited.
        """
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        CiscoSSHConnection.disable_paging(self, command="terminal length 0")
