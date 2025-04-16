from netmiko.cisco_base_connection import CiscoBaseConnection


class TelcoSystemsBinosBase(CiscoBaseConnection):

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging()

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        raise NotImplementedError


class TelcoSystemsBinosSSH(TelcoSystemsBinosBase):
    pass


class TelcoSystemsBinosTelnet(TelcoSystemsBinosBase):
    pass
