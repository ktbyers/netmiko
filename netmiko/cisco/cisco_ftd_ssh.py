"""Subclass specific to Cisco FTD."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def check_enable_mode(self, **kwargs):
        """The FTD CLI has multiple modes of operation, but none of them map directly to "enable mode". Unlike on most
        Cisco devices, it's not expected that you would virtually always want to switch to another mode upon login.
        Therefore, this method simply returns True.

        For more info, see the  Cisco Firepower Threat Defense Command Reference:
        https://www.cisco.com/c/en/us/td/docs/security/firepower/command_ref/b_Command_Reference_for_Firepower_Threat_Defense/using_the_FTD_CLI.html
        """
        return True

    def disable_paging(self, **kwargs):
        """The FTD CLI does not feature paging"""
        pass

    def set_terminal_width(self, **kwargs):
        """The FTD CLI terminal width is not configurable"""
        pass
