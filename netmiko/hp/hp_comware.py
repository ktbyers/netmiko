import re
from typing import Union, Sequence, Iterator, TextIO, Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection


class HPComwareBase(CiscoSSHConnection):
    def __init__(self, **kwargs: Any) -> None:
        # Comware doesn't have a way to set terminal width which breaks cmd_verify
        global_cmd_verify = kwargs.get("global_cmd_verify")
        if global_cmd_verify is None:
            kwargs["global_cmd_verify"] = False
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        # Comware can have a banner that prompts you to continue
        # 'Press Y or ENTER to continue, N to exit.'
        data = self._test_channel_read(pattern=r"to continue|[>\]]")
        if "continue" in data:
            self.write_channel("\n")
            self._test_channel_read(pattern=r"[>\]]")

        self.set_base_prompt()
        command = "screen-length disable"
        self.disable_paging(command=command)

    def config_mode(
        self, config_command: str = "system-view", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "return", pattern: str = r">") -> str:
        """Exit config mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(
        self, check_string: str = "]", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = None,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"\]",
        bypass_commands: Optional[str] = None,
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            read_timeout=read_timeout,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
            cmd_verify=cmd_verify,
            enter_config_mode=enter_config_mode,
            error_pattern=error_pattern,
            terminator=terminator,
            bypass_commands=bypass_commands,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "]",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
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
            pattern=pattern,
        )

        # Strip off any leading RBM_. characters for firewall HA
        prompt = re.sub(r"^RBM_.", "", prompt, flags=re.M)

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
        check_state: bool = True,
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

    def cleanup(self, command: str = "quit") -> None:
        return super().cleanup(command=command)

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
