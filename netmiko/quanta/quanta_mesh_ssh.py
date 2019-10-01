from netmiko.cisco_base_connection import CiscoSSHConnection


class QuantaMeshSSH(CiscoSSHConnection):
    def disable_paging(self, command="no pager", delay_factor=1):
        """Disable paging"""
        return super().disable_paging(command=command)

    def config_mode(self, config_command="configure"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)

    def save_config(
        self,
        cmd="copy running-config startup-config",
        confirm=False,
        confirm_response="",
    ):
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
