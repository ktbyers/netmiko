"""Dell Force10 Driver - supports DNOS9."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""
    def cleanup(self):
        """Gracefully exit the SSH session."""
        self.exit_config_mode()
        self.write_channel("exit\n")
