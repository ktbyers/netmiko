from typing import Any, Optional
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoTimeoutException


class AdtranOSBase(CiscoBaseConnection):
    prompt_pattern = r"[>#]"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        cmd = "terminal width 132"
        self.set_terminal_width(command=cmd, pattern=cmd)

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )

        # Check if in enable mode already.
        if check_state and self.check_enable_mode():
            return output

        # Send "enable" mode command
        self.write_channel(self.normalize_cmd(cmd))
        try:
            # Read the command echo
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

            # Search for trailing prompt or password pattern
            output += self.read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )

            # Send the "secret" in response to password pattern
            if re.search(pattern, output):
                self.write_channel(self.normalize_cmd(self.secret))

                # Handle the fallback to local authentication case
                fallback_pattern = r"Falling back"
                new_output = self.read_until_prompt_or_pattern(
                    pattern=fallback_pattern, re_flags=re_flags
                )
                output += new_output

                if "Falling back" in new_output:
                    self.write_channel(self.normalize_cmd(self.secret))
                    output += self.read_until_prompt()

            # Search for terminating pattern if defined
            if enable_pattern and not re.search(enable_pattern, output):
                output += self.read_until_pattern(pattern=enable_pattern)
            else:
                if not self.check_enable_mode():
                    raise ValueError(msg)

        except NetmikoTimeoutException:
            raise ValueError(msg)

        return output

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "config term", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "end", pattern: str = "#") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )


class AdtranOSSSH(AdtranOSBase):
    pass


class AdtranOSTelnet(AdtranOSBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
