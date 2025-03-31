import re
from typing import Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection

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
        # Clear the read buffer
        # time.sleep(0.3 * self.global_delay_factor)
        # self.clear_buffer()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "",
        enable_pattern: Optional[str] = r"[Pp]assword:",
        check_state: bool = True,
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
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

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

        if not self.check_config_mode(
            check_string=USER_PROMPT, pattern=USER_MODE_REGEX
        ):
            # If we are here, we did not make it back to user mode.
            raise ValueError("Failed to exit configuration mode")
        return output

    def check_config_mode(
        self,
        check_string: str = CONFIG_PROMPT,
        pattern: str = CONFIG_MODE_REGEX,
        force_regex: bool = True,
    ) -> bool:
        """Check if the device is in configuration mode"""

        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

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
        """Saves Config."""
        if confirm:
            output = self._send_command_timing_str(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
            if confirm_response:
                output += self._send_command_timing_str(
                    confirm_response, strip_prompt=False, strip_command=False
                )
            else:
                # Send enter by default
                output += self._send_command_timing_str(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self._send_command_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
                read_timeout=100.0,
            )
        return output
