from typing import Any, Union, List, Dict, Optional
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class MikrotikBase(NoEnable, CiscoSSHConnection):
    """Common Methods for Mikrotik RouterOS and SwitchOS"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"

        self._in_config_mode = False

        return super().__init__(**kwargs)

    def session_preparation(self, *args: Any, **kwargs: Any) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"\].*>")
        self.set_base_prompt()

    def _modify_connection_params(self) -> None:
        """Append login options to username
        c: disable console colors
        e: enable dumb terminal mode
        t: disable auto detect terminal capabilities
        w511: set term width
        h4098: set term height
        """
        self.username += "+ctw511h4098"

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Mikrotik does not have paging by default."""
        return ""

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """No save command, all configuration is atomic"""
        return ""

    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        """No configuration mode on Mikrotik"""
        self._in_config_mode = True
        return ""

    def check_config_mode(self, check_string: str = "", pattern: str = "") -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return self._in_config_mode

    def exit_config_mode(self, exit_config: str = ">", pattern: str = "") -> str:
        """No configuration mode on Mikrotik"""
        self._in_config_mode = False
        return ""

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output.

        Mikrotik just does a lot of formatting/has ansi escape codes in output so
        we need a special handler here.

        There can be two trailing instances of the prompt probably due to
        repainting.
        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]

        # Drop the first trailing prompt
        if self.base_prompt in last_line:
            a_string = self.RESPONSE_RETURN.join(response_list[:-1])
            a_string = a_string.rstrip()
            # Now it should be just normal: call the parent method
            a_string = super().strip_prompt(a_string)
            return a_string.strip()
        else:
            # Unexpected just return the original string
            return a_string

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Strip the trailing space off."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def send_command_timing(  # type: ignore
        self,
        command_string: str,
        cmd_verify: bool = True,
        **kwargs: Any,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Force cmd_verify to be True due to all of the line repainting"""
        return super()._send_command_timing_str(
            command_string=command_string, cmd_verify=cmd_verify, **kwargs
        )


class MikrotikRouterOsSSH(MikrotikBase):
    """Mikrotik RouterOS SSH driver."""

    pass


class MikrotikSwitchOsSSH(MikrotikBase):
    """Mikrotik SwitchOS SSH driver."""

    pass
