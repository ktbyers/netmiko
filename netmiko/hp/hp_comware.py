import time
import re
from typing import Union, Sequence, TextIO, Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection


class HPComwareBase(CiscoSSHConnection):
    def __init__(self, **kwargs: Any) -> None:
        # Comware doesn't have a way to set terminal width which breaks cmd_verify
        global_cmd_verify = kwargs.get("global_cmd_verify")
        if global_cmd_verify is None:
            kwargs["global_cmd_verify"] = False
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        i = 1
        while i <= 4:
            # Comware can have a banner that prompts you to continue
            # 'Press Y or ENTER to continue, N to exit.'
            time.sleep(0.5 * delay_factor)
            self.write_channel("\n")
            i += 1

        time.sleep(0.3 * delay_factor)
        self.clear_buffer()
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        command = self.RETURN + "screen-length disable"
        self.disable_paging(command=command)
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(
        self, config_command: str = "system-view", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "return", pattern: str = r">") -> str:
        """Exit config mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string: str = "]", pattern: str = "") -> bool:
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        exit_config_mode: bool = True,
        delay_factor: float = 1.0,
        max_loops: int = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"\]",
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
            cmd_verify=cmd_verify,
            enter_config_mode=enter_config_mode,
            error_pattern=error_pattern,
            terminator=terminator,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "]",
        delay_factor: float = 1.0,
    ) -> str:
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

        # Strip off leading character
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(
        self,
        cmd: str = "system-view",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """enable mode on Comware is system-view."""
        return self.config_mode(config_command=cmd)

    def exit_enable_mode(self, exit_command: str = "return") -> str:
        """enable mode on Comware is system-view."""
        return self.exit_config_mode(exit_config=exit_command)

    def check_enable_mode(self, check_string: str = "]") -> bool:
        """enable mode on Comware is system-view."""
        return self.check_config_mode(check_string=check_string)

    def save_config(
        self, cmd: str = "save force", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class HPComwareSSH(HPComwareBase):
    pass


class HPComwareTelnet(HPComwareBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
