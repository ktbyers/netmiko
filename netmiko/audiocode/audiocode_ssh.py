from typing import Any, Optional, Sequence, Iterator, TextIO, Union, List
import time
import re
from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable


class AudiocodeBase(BaseConnection):
    """Common Methods for AudioCode Drivers."""

    prompt_pattern = r"[>#]"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:

        if pattern is None:
            pattern = rf"\*?{self.prompt_pattern}"

        if pattern:
            prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern)
        else:
            prompt = self.find_prompt(delay_factor=delay_factor)

        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")

        # If all we have is the 'terminator' just use that :-(
        if len(prompt) == 1:
            self.base_prompt = prompt
        else:
            # Audiocode will return a prompt with * in it in certain
            # situations: 'MYDEVICE*#', strip this off.
            if "*#" in prompt or "*>" in prompt:
                self.base_prompt = prompt[:-2]
            else:
                # Strip off trailing terminator
                self.base_prompt = prompt[:-1]
        return self.base_prompt

    def find_prompt(
        self,
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:

        if pattern is None:
            pattern = rf"\*?{self.prompt_pattern}"
        return super().find_prompt(
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def _enable_paging(
        self,
        delay_factor: Optional[float] = 0.5,
    ) -> str:
        return ""

    def check_config_mode(
        self,
        check_string: str = r"(?:\)#|\)\*#)",
        pattern: str = r"..#",
        force_regex: bool = True,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            self._enable_paging()
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = "#",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#") -> str:
        output = ""
        max_exit_depth = 10
        if self.check_config_mode():
            # Keep "exitting" until out of config mode
            for _ in range(max_exit_depth):
                self.write_channel(self.normalize_cmd(exit_config))

                # Make sure you read until you detect the command echo (avoid getting out of sync)
                if self.global_cmd_verify is not False:
                    output += self.read_until_pattern(
                        pattern=re.escape(exit_config.strip())
                    )
                if pattern:
                    output += self.read_until_pattern(pattern=pattern)
                else:
                    output += self.read_until_prompt(read_entire_line=True)

                if not self.check_config_mode():
                    # No longer in config mode
                    break
            else:  # no-break
                raise ValueError("Failed to exit configuration mode")
        return output

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """Exit enable mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = None,
        delay_factor: Optional[float] = 1.0,
        max_loops: Optional[int] = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"\*?#",
        bypass_commands: Optional[str] = None,
    ) -> str:
        if enter_config_mode and config_mode_command is None:
            msg = """
send_config_set() for the Audiocode drivers require that you specify the
config_mode_command. For example, config_mode_command="configure system"
(or "configure voip" or "configure network" etc.)
            """
            raise ValueError(msg)
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

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves the running configuration."""

        self.enable()
        if confirm:
            output = self._send_command_timing_str(command_string=cmd)
            if confirm_response:
                output += self._send_command_timing_str(confirm_response)
            else:
                # Send enter by default
                output += self._send_command_timing_str(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self._send_command_str(command_string=cmd)
        return output

    def _reload_device(
        self,
        cmd_save: str = "reload now",
        cmd_no_save: str = "reload without-saving",
        reload_save: bool = True,
    ) -> str:
        """Reloads the device."""
        if reload_save:
            cmd = cmd_save
        else:
            cmd = cmd_no_save
        self._enable_paging()
        self.enable()
        return self._send_command_timing_str(command_string=cmd)


class Audiocode72Base(AudiocodeBase):
    """Common Methods for AudioCodes running 7.2 CLI."""

    def disable_paging(
        self,
        command: str = "",
        delay_factor: Optional[float] = 0.5,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:

        if command:
            return super().disable_paging(
                command=command,
                delay_factor=delay_factor,
                cmd_verify=cmd_verify,
                pattern=pattern,
            )
        else:
            command_list: List[str] = [
                "cli-settings",
                "window-height 0",
            ]

        self.enable()
        assert isinstance(delay_factor, float)
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        return self.send_config_set(
            config_commands=command_list,
            config_mode_command="config system",
        )

    def _enable_paging(
        self,
        delay_factor: Optional[float] = 0.5,
    ) -> str:
        """This is designed to re-enable window paging."""

        command_list: List[str] = [
            "cli-settings",
            "window-height automatic",
        ]
        self.enable()
        assert isinstance(delay_factor, float)
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()

        return self.send_config_set(
            config_commands=command_list,
            config_mode_command="config system",
        )


class Audiocode72Telnet(Audiocode72Base):
    pass


class Audiocode72SSH(Audiocode72Base):
    pass


class AudiocodeBase66(AudiocodeBase):
    """Audiocode this applies to 6.6 Audiocode Firmware versions."""

    def disable_paging(
        self,
        command: str = "",
        delay_factor: Optional[float] = 0.5,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:

        if command:
            return super().disable_paging(
                command=command,
                delay_factor=delay_factor,
                cmd_verify=cmd_verify,
                pattern=pattern,
            )
        else:
            command_list: List[str] = [
                "cli-terminal",
                "set window-height 0",
            ]

            self.enable()
            assert isinstance(delay_factor, float)
            delay_factor = self.select_delay_factor(delay_factor)
            time.sleep(delay_factor * 0.1)
            self.clear_buffer()
            return self.send_config_set(
                config_commands=command_list,
                config_mode_command="config system",
            )

    def _enable_paging(
        self,
        delay_factor: Optional[float] = 0.5,
    ) -> str:

        command_list: List[str] = [
            "cli-terminal",
            "set window-height 100",
        ]
        self.enable()
        assert isinstance(delay_factor, float)
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()

        return self.send_config_set(
            config_commands=command_list,
            config_mode_command="config system",
        )


class Audiocode66SSH(AudiocodeBase66):
    pass


class Audiocode66Telnet(AudiocodeBase66):
    pass


class AudiocodeShellBase(NoEnable, AudiocodeBase):
    """Audiocode this applies to 6.6 Audiocode Firmware versions that only use the Shell."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.write_channel(self.RETURN)
        self.write_channel(self.RETURN)
        self._test_channel_read(pattern=r"/>")
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r"/>",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"/>",
    ) -> str:
        prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern)
        pattern = pri_prompt_terminator
        if not re.search(pattern, prompt):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")
        else:
            # Strip off trailing terminator
            self.base_prompt = prompt
            return self.base_prompt

    def find_prompt(
        self,
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"/>",
    ) -> str:
        return super().find_prompt(
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = None,
        delay_factor: Optional[float] = 1.0,
        max_loops: Optional[int] = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"/.*>",
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

    def config_mode(
        self, config_command: str = "", pattern: str = r"/.*>", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = r"/CONFiguration>",
        pattern: str = r"/.*>",
        force_regex: bool = True,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_config_mode(self, exit_config: str = "..", pattern: str = r"/>") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def disable_paging(
        self,
        command: str = "",
        delay_factor: Optional[float] = 0.5,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Not supported"""
        return ""

    def save_config(
        self,
        cmd: str = "SaveConfiguration",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def _reload_device(
        self,
        cmd_save: str = "SaveAndReset",
        cmd_no_save: str = "ReSetDevice",
        reload_save: bool = True,
    ) -> str:
        """Reloads the device."""
        return super()._reload_device(
            cmd_save=cmd_save, cmd_no_save=cmd_no_save, reload_save=reload_save
        )

    def _enable_paging(
        self,
        delay_factor: Optional[float] = 0.5,
    ) -> str:
        """Not supported"""
        return ""

    def strip_command(self, command_string: str, output: str) -> str:
        # Support for Audiocode_Shell.
        pattern = r"^SIP.*[\s\S]?PING.*>?.*[\s\S]?.*>?$"
        output = re.sub(pattern, "", output, flags=re.M)

        cmd = command_string.strip()
        pattern = re.escape(cmd)
        output = re.sub(pattern, "", output, flags=re.M)
        return super().strip_command(command_string=command_string, output=output)

    def strip_prompt(self, a_string: str) -> str:
        pattern = r"^/>?"
        a_string = re.sub(pattern, "", a_string, flags=re.M)
        return super().strip_prompt(
            a_string=a_string,
        )


class AudiocodeShellSSH(AudiocodeShellBase):
    pass


class AudiocodeShellTelnet(AudiocodeShellBase):
    pass
