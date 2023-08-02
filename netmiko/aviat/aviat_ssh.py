from netmiko.cisco_base_connection import CiscoSSHConnection
import re
from netmiko import log


class AviatWTMSSH(CiscoSSHConnection):
    """Aviat WTM Outdoor Radio support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()

    def find_prompt(self, delay_factor: float = 1.0, pattern: str = r"[$>#]") -> str:
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def exit_config_mode(
        self,
        exit_config: str = "end",
        pattern: str = r"Uncommitted changes.*CANCEL\]",
        confirm: str = "yes",
    ) -> str:
        """
        Exits from configuration mode. Overwritten from base class because the device
        prompts to save uncommitted changes when exiting config mode and requires user confirmation.
        If 'Uncommitted changes found' is detected in the output, the function sends a 'confirm' command.

        Args:
        exit_config (str, optional): Command to exit configuration mode. Default is 'end'.
        pattern (str, optional): Regex pattern to match the uncommitted changes prompt.
            Default is 'Uncommitted changes.*CANCEL\]'.
        confirm (str, optional): Command to confirm uncommitted changes. Default is 'yes'.

        Returns:
        str: Output from the device after exiting configuration mode.
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            # Read until we detect the uncommitted changes pattern or the usual prompt pattern
            output += self.read_until_pattern(pattern=pattern + "|#")
            # If uncommitted changes were found, confirm them
            if "Uncommitted changes found" in output:
                self.write_channel(self.normalize_cmd(confirm))
                output += self.read_until_pattern(pattern=r"[$>#]")
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug(f"exit_config_mode: {output}")
        return output

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )
