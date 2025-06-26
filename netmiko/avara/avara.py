import re
from typing import Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import NetmikoTimeoutException

# Example Prompts:
# - User:   `DEVNAME % `
# - Config: `DEVNAME* % `

USER_PROMPT: str = " %"
CONFIG_PROMPT: str = "* %"
# The user prompt regex needs to exclude matches with the '*'
# Otherwise, it will also match the config prompt.
USER_MODE_REGEX: str = r"[^\*]\s%"
CONFIG_MODE_REGEX: str = r"\*\s%"


class AvaraSSH(CiscoSSHConnection):
    """Avara SSH Driver for Netmiko."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established.

        Returns:
            None
        """
        self._test_channel_read(pattern=USER_MODE_REGEX)
        self.base_prompt = self.find_prompt()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "assword",
        enable_pattern: Optional[str] = None,
        check_state: bool = False,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode, which is configuration mode on Avara devices.

        Args:
            cmd: Command to enter enable mode
            pattern: Pattern to search for password prompt
            enable_pattern: Pattern to search for enable mode prompt
            re_flags: Regular expression flags

        Returns:
            str: Output of entering enable mode
        """
        error_msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        output = ""
        if not self.check_config_mode():
            try:
                # Send "enable" mode command
                self.write_channel(self.normalize_cmd(cmd))

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
                    output += self.read_channel_timing(read_timeout=0)

                    if not self.check_config_mode():
                        raise ValueError(error_msg)

            except NetmikoTimeoutException:
                raise ValueError(error_msg)

            return output
        return "Config mode already enabled."

    def config_mode(self):
        """Redirect config mode to enable mode"""
        return self.enable()

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """
        Exit from enable mode.
        Args:
            exit_command: Command to exit enable mode

        Returns:
            str: Output of the exit command

        Raises:
            ValueError: If unable to exit enable mode
        """
        return self.exit_config_mode(exit_config=exit_command)

    def check_config_mode(
        self,
        check_string: str = CONFIG_PROMPT,
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """
        Check if the device is in configuration mode.

        Args:
            check_string: String pattern to check for configuration mode. Defaults to CONFIG_PROMPT.
            pattern: Additional pattern to check for configuration mode. Defaults to empty string.
            force_regex: Whether to use regex for matching. Defaults to False.

        Returns:
            bool: True if device is in configuration mode, False otherwise.
        """
        # Silence warnings
        _pattern = pattern
        _force_regex = force_regex

        self.write_channel(self.RETURN)
        output = self.read_channel_timing(read_timeout=0.5)
        return check_string in output

    def send_config_set(
        self,
        config_commands: Any = None,
        exit_config_mode: bool = False,
        terminator: str = "%",
        **kwargs: Any,
    ) -> str:
        """
        Send configuration commands to the device.

        Args:
            config_commands: A string or list of strings containing configuration commands.
            exit_config_mode: If True, exit configuration mode when complete.
            **kwargs: Additional arguments to pass to send_config_set method.

        Returns:
            str: The output of the configuration commands.
        """
        # if not self.check_config_mode():
        #     self.enable()

        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            terminator=terminator,
            **kwargs,
        )

    def exit_config_mode(
        self, exit_config: str = "disable", pattern: str = r"Edit mode exited\."
    ) -> str:
        """Exit from configuration mode.

        Args:
            exit_config: Command to exit configuration mode
            pattern: Pattern to terminate reading of channel

        Returns:
            str: The output of the exit configuration commands.
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self, cmd: str = "save flash", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """
        Save the configuration to flash memory.
        This method first applies any pending configuration edits using the "apply" command,
        and then saves the configuration to flash memory using the parent class's save_config method.

        Args:
            cmd: The command to save the configuration. Default is "save flash".
            confirm: Whether confirmation is required or not. Default is False.
            confirm_response: The response to confirmation prompt. Default is empty string.

        Returns:
            str: The output of the save configuration command.
        """

        # Apply Edits
        self.send_command(command_string="apply", expect_string="Edits applied.")

        # Save configuration to flash
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )

    def disconnect(self) -> None:
        """
        Attempts to gracefully close the SSH connection to the device
        and the log files. Any exceptions during closure are suppressed.

        Returns:
            None
        """

        try:
            if self.remote_conn:
                self.remote_conn.close()
            if self.remote_conn_pre:
                self.remote_conn_pre.close()
        except Exception:
            pass
        finally:
            self.remote_conn_pre = None
            self.remote_conn = None
            if self.session_log:
                self.session_log.close()
