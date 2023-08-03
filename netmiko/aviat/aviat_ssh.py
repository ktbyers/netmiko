from netmiko.cisco_base_connection import CiscoSSHConnection
import re
from netmiko import log
from typing import Optional


class AviatWTMSSH(CiscoSSHConnection):
    """Aviat WTM Outdoor Radio support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.disable_paging()
        self.set_base_prompt()

    def disable_paging(
        self,
        commands: list = ["session paginate false"],
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        return self.send_config_set(
            config_commands=commands,
        )

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

    def enable(
        self,
        cmd: str = "",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Aviat WTM Outdoor Radio does not have an enable mode"""
        raise NotImplementedError

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """
        Aviat WTM Outdoor Radio does not possess a 'save config' command. Instead,
        when changes are detected in config mode, the user is prompted to commit these
        changes. This happens either when trying to exit or when the 'commit'
        command is typed.
        """
        raise NotImplementedError
