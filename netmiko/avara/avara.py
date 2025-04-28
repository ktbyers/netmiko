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
        """Prepare the session after the connection has been established."""
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

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """Exit enable mode.

        :param exit_command: Command that exits the session from privileged mode
        :type exit_command: str
        """

        output = ""
        self.write_channel(self.normalize_cmd(exit_command))
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if self.global_cmd_verify is not False:
            output += self.read_until_pattern(pattern=re.escape(exit_command.strip()))

        output += self.read_until_pattern(pattern=USER_MODE_REGEX)

        if not self.check_config_mode(check_string=USER_PROMPT):
            # If we are here, we did not make it back to user mode.
            raise ValueError("Failed to exit configuration mode")
        return output

    def check_config_mode(
        self,
        check_string: str = CONFIG_PROMPT,
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Check if the device is in configuration mode"""

        self.write_channel(self.RETURN)
        output = self.read_channel_timing(read_timeout=0.5)
        return check_string in output

    def send_config_set(
        self, config_commands: Any = None, exit_config_mode: bool = False, **kwargs: Any
    ) -> str:
        """Send configuration commands to the device."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def save_config(
        self, cmd: str = "save flash", confirm: bool = False, confirm_response: str = ""
    ) -> str:
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
        Try to gracefully close the session.
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
