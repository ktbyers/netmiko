"""Subclass specific to Cisco Viptela."""

from typing import Union, Sequence, Iterator, TextIO, Any
import re

from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoViptelaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco Viptela."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="paginate false")

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def commit(self, confirm: bool = False, confirm_response: str = "") -> str:
        cmd = "commit"
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def config_mode(
        self,
        config_command: str = "conf terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def exit_config_mode(self, exit_config: str = "end", pattern: str = r"#") -> str:
        """
        Exit from configuration mode.

        Viptela might have the following in the output (if no 'commit()' occurred.

        Uncommitted changes found, commit them? [yes/no/CANCEL]
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            if not re.search(pattern, output, flags=re.M):
                uncommit_pattern = r"Uncommitted changes found"
                new_pattern = f"({pattern}|{uncommit_pattern})"
                output += self.read_until_pattern(pattern=new_pattern)
                # Do not save 'uncommited changes'
                if uncommit_pattern in output:
                    self.write_channel(self.normalize_cmd("no"))
                    output += self.read_until_pattern(pattern=pattern)

            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def save_config(
        self, cmd: str = "commit", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config"""
        raise NotImplementedError
