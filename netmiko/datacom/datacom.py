from netmiko.cisco_base_connection import CiscoBaseConnection


class DataComBase(CiscoBaseConnection):
    def config_mode(
        self,
        config_command: str = "config terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def save_config(
        self, cmd: str = "commit", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config Using Copy Run Start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

class DataComSSH(DataComBase):
    """DataCom SSH driver."""
    pass


class DataComTelnet(DataComBase):
    """DataCom telnet driver."""
    pass