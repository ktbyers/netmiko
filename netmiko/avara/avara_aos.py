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


class AvaraAosSSH(CiscoSSHConnection):
    """Avara AOS SSH Driver for Netmiko."""

    def session_preparation(self) -> None:
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
        """Enter enable mode, which is configuration mode on Avara AOS devices."""
        error_msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        output = ""
        if not self.check_config_mode():
            try:
                self.write_channel(self.normalize_cmd(cmd))

                if self.global_cmd_verify is not False:
                    output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

                output += self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags
                )

                if re.search(pattern, output):
                    self.write_channel(self.normalize_cmd(self.secret))
                    output += self.read_channel_timing(read_timeout=0)

                    if not self.check_config_mode():
                        raise ValueError(error_msg)

            except NetmikoTimeoutException:
                raise ValueError(error_msg)

            return output
        return "Config mode already enabled."

    def config_mode(
        self,
        config_command: str = "enable",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Redirect config_mode to enable — Avara AOS has no separate config mode."""
        return self.enable()

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        return self.exit_config_mode(exit_config=exit_command)

    def check_config_mode(
        self,
        check_string: str = CONFIG_PROMPT,
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
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
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            terminator=terminator,
            **kwargs,
        )

    def exit_config_mode(
        self, exit_config: str = "disable", pattern: str = r"Edit mode exited\."
    ) -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self, cmd: str = "save flash", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Apply pending edits then save configuration to flash."""
        self.send_command(command_string="apply", expect_string="Edits applied.")
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)
