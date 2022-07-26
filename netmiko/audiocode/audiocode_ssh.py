from typing import Any, Optional, Sequence, TextIO, Union, List
from netmiko.base_connection import BaseConnection
import time
import re


class AudiocodeBaseSSH(BaseConnection):
    """Common Methods for AudioCodes running 7.2 CLI for SSH."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"\*?(#|>)",
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def find_prompt(
        self,
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"\*?(#|>)",
    ) -> str:
        return super().find_prompt(
            delay_factor=delay_factor,
            pattern=pattern,
        )

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

    def check_config_mode(
        self,
        check_string: str = r"(\)#|\)\*#)",
        pattern: str = "#",
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
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode.

        :param cmd: Device command to enter enable mode

        :param pattern: pattern to search for indicating device is waiting for password

        :param enable_pattern: pattern indicating you have entered enable mode

        :param re_flags: Regular expression flags used in conjunction with pattern
        """
        return super().enable(
            cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#") -> str:
        """Exit from configuration mode.

        :param exit_config: Command to exit configuration mode
        :type exit_config: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """Exit enable mode.

        :param exit_command: Command that exits the session from privileged mode
        :type exit_command: str
        """
        return super().exit_enable_mode(exit_command=exit_command)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = None,
        delay_factor: Optional[float] = 1.0,
        max_loops: Optional[int] = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = False,
        error_pattern: str = "",
        terminator: str = r"\*?#",
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
        cmd: str = "reload now",
        reload_save: bool = True,
    ) -> str:
        """Reloads the device."""
        if reload_save is not True:
            cmd = "reload without-saving"
        self._enable_paging()
        self.enable()
        return self._send_command_timing_str(command_string=cmd)


class AudiocodeBaseTelnet(AudiocodeBaseSSH):
    """Audiocode Telnet driver."""

    pass


class Audiocode66SSH(AudiocodeBaseSSH):
    """Audiocode this applies to 6.6 Audiocode Firmware versions."""

    def disable_paging(
        self,
        disable_window_config=[
            "config system",
            "cli-terminal",
            "set window-height 0",
            "exit",
        ],
        delay_factor=0.5,
    ):
        """This is designed to disable window paging which prevents paged command
        output from breaking the script.

        :param disable_window_config: Command, or list of commands, to execute.
        :type disable_window_config: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        """
        return super().disable_paging(
            disable_window_config=disable_window_config, delay_factor=delay_factor
        )

    def _enable_paging(
        self,
        enable_window_config=[
            "config system",
            "cli-terminal",
            "set window-height 100",
            "exit",
        ],
        delay_factor=0.5,
    ):
        """This is designed to reenable window paging

        :param enable_window_config: Command, or list of commands, to execute.
        :type enable_window_config: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        """
        return super()._enable_paging(
            enable_window_config=enable_window_config, delay_factor=delay_factor
        )


class Audiocode66Telnet(Audiocode66SSH):
    """Audiocode Telnet driver."""

    pass


class AudiocodeShellSSH(AudiocodeBaseSSH):
    """Audiocode this applies to 6.6 Audiocode Firmware versions that only use the Shell."""

    def session_preparation(self):
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
        pri_prompt_terminator=r"/>",
        alt_prompt_terminator="",
        delay_factor=1.0,
        pattern=r"/>",
    ):
        """Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without > or #).

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt

        :param delay_factor: See __init__: global_delay_factor

        :param pattern: Regular expression pattern to search for in find_prompt() call
        """
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
        pattern: str = r"/>",
    ) -> str:
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        :param pattern: Regular expression pattern to determine whether prompt is valid

        :param confirm_pattern: Regular expression pattern to confirm prompt was found by auto discovery.
        """
        return super().find_prompt(
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def enable(self, cmd="", pattern="", re_flags=re.IGNORECASE):
        """Not supported"""
        pass

    def check_enable_mode(self, check_string=r"/>"):
        """Check if in enable mode. Return boolean.

        :param check_string: Identification of privilege mode from device
        :type check_string: str
        """
        return super().check_enable_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command=""):
        """Not supported"""
        pass

    def send_config_set(
        self,
        config_commands=None,
        exit_config_mode: bool = True,
        read_timeout: float = None,
        delay_factor: float = 1.0,
        max_loops: int = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"/.*>",
        bypass_commands: str = None,
    ) -> str:

        if config_mode_command is None:
            msg = """
send_config_set() for the audiocode driver requires that you specify the
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

    def config_mode(
        self, config_command: str = "", pattern: str = r"/.*>", re_flags: int = 0
    ) -> str:
        """Enter into config_mode.

        :param config_command: Configuration command to send to the device
        :type config_command: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param re_flags: Regular expression flags
        :type re_flags: RegexFlag
        """
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = r"/CONFiguration>",
        pattern: str = r"/.*>",
        force_regex: bool = True,
    ) -> bool:
        """Checks if the device is in configuration mode or not.

        :param check_string: Identification of configuration mode from the device
        :type check_string: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_config_mode(self, exit_config: str = "..", pattern: str = r"/>") -> str:
        """Exit from configuration mode.

        :param exit_config: Command to exit configuration mode
        :type exit_config: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def disable_paging(self):
        """Not supported"""
        pass

    def save_config(self, cmd="SaveConfiguration", confirm=False, confirm_response=""):
        """Saves the running configuration.

        :param cmd: Command to save configuration
        :type cmd: str

        :param confirm: Command if confirmation prompt is required
        :type confirm: bool

        :param confirm_response: Command if confirm response required to further script
        :type confirm response: str

        """
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def _reload_device(
        self,
        reload_device=True,
        reload_save=True,
        cmd_save="SaveAndReset",
        cmd_no_save="ReSetDevice",
        reload_message="Resetting the board",
    ):
        """Reloads the device.

        :param reload_device: Boolean to determine if reload should occur.
        :type reload_device: bool

        :param reload_device: Boolean to determine if reload with saving first should occur.
        :type reload_device: bool

        :param cmd_save: Command to reload device with save.  Options are "reload now" and "reload if-needed".
        :type cmd_save: str

        :param cmd_no_save: Command to reload device.  Options are "reload without-saving", "reload without-saving in [minutes]".
        :type cmd_no_save: str

        :param reload_message: This is the pattern by which the reload is detected.
        :type reload_message: str

        """
        return super()._reload_device(
            reload_device=reload_device,
            reload_save=reload_save,
            cmd_save=cmd_save,
            cmd_no_save=cmd_no_save,
            reload_message=reload_message,
        )

    def _device_terminal_exit(self, command="exit"):
        """This is for accessing devices via terminal. It first reenables window paging for
        future use and exits the device before you send the disconnect method"""
        return super()._device_terminal_exit(command=command)

    def _enable_paging(self):
        """Not supported"""
        pass

    def strip_command(self, command_string: str, output: str) -> str:
        """
        Strip command_string from output string

        Cisco IOS adds backspaces into output for long commands (i.e. for commands that line wrap)

        :param command_string: The command string sent to the device
        :type command_string: str

        :param output: The returned output as a result of the command string sent to the device
        :type output: str
        """
        # Support for Audiocode_Shell.
        pattern = r"^SIP.*[\s\S]?PING.*>?.*[\s\S]?.*>?$"
        output = re.sub(pattern, "", output, flags=re.M)

        cmd = command_string.strip()
        pattern = rf"{cmd}"
        output = re.sub(pattern, "", output, flags=re.M)

        return super().strip_command(command_string=command_string, output=output)

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output.

        :param a_string: Returned string from device
        :type a_string: str
        """
        pattern = r"^/>?"
        a_string = re.sub(pattern, "", a_string, flags=re.M)

        return super().strip_prompt(
            a_string=a_string,
        )


class AudiocodeShellTelnet(AudiocodeShellSSH):
    """Audiocode this applies to 6.6 Audiocode Firmware versions that only use the Shell."""

    pass
