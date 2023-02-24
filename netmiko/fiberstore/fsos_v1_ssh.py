from netmiko.cisco_base_connection import CiscoBaseConnection


class FsosV1SSH(CiscoBaseConnection):
    """
    Implements methods for communicating with Fsos v1.
    
    Mostly conforms to Cisco IOS style syntax with a few minor changes.
    """
    
   def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.disable_paging()
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = base_prompt
        return self.base_prompt

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self, cmd: str = "copy running-config startup-config", confirm: bool = True, confirm_response: str = "startup.cfg"
    ) -> str:
        """Saves Config Using copy run start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )