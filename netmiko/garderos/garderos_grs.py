from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import ConfigInvalidException
from time import sleep
from typing import (
    Optional,
    Any,
    List,
    Dict,
    Sequence,
    Iterator,
    TextIO,
    Union,
)


class GarderosGrsSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established"""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt(pri_prompt_terminator="#")
        self.clear_buffer()

    def send_command(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Add strip() command to output of send_command()"""

        # First check if command contains a newline/carriage-return.
        # This is not allowed in Garderos GRS
        command_string = args[0] if args else kwargs["command_string"]
        if "\n" in command_string or "\r" in command_string:
            raise ValueError(
                f"The command contains an illegal newline/carriage-return: {command_string}"
            )

        # Send command to device
        result = super().send_command(*args, **kwargs)

        # Optimize output of strings
        if isinstance(result, str):
            result = result.strip()
        return result

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self,
        config_command: str = "configuration terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "#") -> str:
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def commit(self, commit: str = "commit") -> str:
        """Commit the candidate configuration."""

        if self.check_config_mode():
            raise ValueError("Device is in configuration mode. Please exit first.")

        # Run commit command
        commit_result = self._send_command_str(commit)

        # Verify success
        if "No configuration to commit" in commit_result:
            raise ValueError(
                "No configuration to commit. Please configure device first."
            )
        elif "Values will be reloaded" not in commit_result:
            raise ValueError(f"Commit was unsuccessful. Device said: {commit_result}")

        # Garderos needs a second to apply the config
        # If the "show configuration running" command is executed too quickly after committing
        # it will result in error "No running configuration found."
        sleep(1)
        return commit_result

    def save_config(
        self,
        cmd: str = "write startup-configuration",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config."""

        if self.check_config_mode():
            raise ValueError("Device is in configuration mode. Please exit first.")

        if confirm:
            raise ValueError(
                "Garderos saves the config without the need of confirmation. "
                "Please set variable 'confirm' to False!"
            )

        save_config_result = self._send_command_str(cmd)

        # Verify success
        if "Values are persistently saved to STARTUP-CONF" not in save_config_result:
            raise ValueError(
                f"Saving configuration was unsuccessful. Device said: {save_config_result}"
            )

        return save_config_result

    def _check_linux_mode(self, check_string: str = "]#", pattern: str = "#") -> bool:
        """Checks if the device is in Linux mode or not.

        :param check_string: Identification of configuration mode from the device

        :param pattern: Pattern to terminate reading of channel
        """
        self.write_channel(self.RETURN)
        output = self.read_until_prompt(read_entire_line=True)
        return check_string in output

    def _linux_mode(
        self, linux_command: str = "linux-shell", pattern: str = r"#"
    ) -> str:
        """Enter into Linux mode.

        :param config_command: Linux command to send to the device

        :param pattern: Pattern to terminate reading of channel
        """
        output = ""
        if not self._check_linux_mode():
            self.write_channel(self.normalize_cmd(linux_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self._check_linux_mode():
                raise ValueError("Failed to enter Linux mode.")
        return output

    def _exit_linux_mode(self, exit_linux: str = "exit", pattern: str = "#") -> str:
        """Exit from Linux mode.

        :param exit_config: Command to exit Linux mode

        :param pattern: Pattern to terminate reading of channel
        """
        output = ""
        if self._check_linux_mode():
            self.write_channel(self.normalize_cmd(exit_linux))
            output = self.read_until_pattern(pattern=pattern)
            if self._check_linux_mode():
                raise ValueError("Failed to exit Linux mode")
        return output

    def _send_config_command(
        self,
        command_string: str,
        expect_string: Optional[str] = None,
        read_timeout: float = 10.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        auto_find_prompt: bool = True,
        strip_prompt: bool = True,
        strip_command: bool = True,
        normalize: bool = True,
        use_textfsm: bool = False,
        textfsm_template: Optional[str] = None,
        use_ttp: bool = False,
        ttp_template: Optional[str] = None,
        use_genie: bool = False,
        cmd_verify: bool = True,
    ) -> str:
        """
        Execute a command in configuration mode and raise error if command execution failed.
        Function neither checks if device is configuration mode nor turns on configuration mode.
        """
        # Send command to device
        command_result = self._send_command_str(
            command_string=command_string,
            expect_string=expect_string,
            read_timeout=read_timeout,
            delay_factor=delay_factor,
            max_loops=max_loops,
            auto_find_prompt=auto_find_prompt,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            normalize=normalize,
            use_textfsm=use_textfsm,
            textfsm_template=textfsm_template,
            use_ttp=use_ttp,
            ttp_template=ttp_template,
            use_genie=use_genie,
            cmd_verify=cmd_verify,
        )
        # Verify if configuration command executed successfully
        if command_result != "Set.":
            raise ConfigInvalidException(
                'Error executing configuration command "{}". Device said: {}'.format(
                    command_string, command_result
                )
            )
        return command_result

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
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
        terminator: str = r"#",
        bypass_commands: Optional[str] = None,
    ) -> str:

        # The result of all commands will be collected to config_results
        config_results = ""

        # Set delay_factor to given value
        if delay_factor is None:
            delay_factor = self.select_delay_factor(0)
        else:
            delay_factor = self.select_delay_factor(delay_factor)

        # Verify if config_commands is an array
        if config_commands is None:
            return config_results
        elif isinstance(config_commands, str):
            config_commands = (config_commands,)
        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Go to config mode. Use given config_mode_command if necessary.
        if enter_config_mode:
            if config_mode_command:
                config_results += self.config_mode(config_mode_command)
            else:
                config_results += self.config_mode()

        # Send all commands to the router and verify their successful execution
        for command in config_commands:
            # Verification is done in send_config_command()
            # Will raise error on execution failure
            config_results += self._send_config_command(command)

        if exit_config_mode:
            config_results += self.exit_config_mode()
        return config_results
