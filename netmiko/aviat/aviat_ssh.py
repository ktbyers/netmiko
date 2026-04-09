import re
from typing import Any, Iterator, Optional, Sequence, TextIO, Union
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class AviatWTMSSH(NoEnable, CiscoSSHConnection):
    """Aviat WTM Outdoor Radio support"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_auto_change", False)
        return super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read()
        if self.allow_auto_change:
            self.disable_paging()
            self.commit()
        self.set_base_prompt()

    def disable_paging(
        self,
        command: str = "session paginate false",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        return self.send_config_set(
            config_commands=command,
        )

    def find_prompt(self, delay_factor: float = 1.0, pattern: Optional[str] = r"[$>#]") -> str:
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def exit_config_mode(
        self,
        exit_config: str = "end",
        pattern: str = r"(?:Uncommitted changes|#)",
    ) -> str:
        """Exit configuration mode.

        Raises ValueError if uncommitted changes are detected — call commit() first.
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(exit_config.strip()))
            output += self.read_until_pattern(pattern=pattern)
            if "Uncommitted changes" in output:
                raise ValueError(
                    "Uncommitted changes detected — call commit() before exiting config mode."
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode.")
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

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Send config commands; defaults to not exiting config mode (call commit() explicitly)."""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            **kwargs,
        )

    def commit(self, cmd: str = "commit", read_timeout: float = 120.0) -> str:
        """
        Commit configuration changes on Aviat WTM devices.

        Changes entered in config mode are staged in a candidate buffer and do not
        take effect until committed. The commit command moves changes from candidate
        to running state (and typically saves to flash).

        Must be called from within configuration mode.
        """
        if not self.check_config_mode():
            raise ValueError("Must be in configuration mode to commit.")
        self.write_channel(self.normalize_cmd(cmd))
        output = self.read_until_pattern(pattern=r"\)#", read_timeout=read_timeout)
        return output

    def save_config(self, cmd: str = "", confirm: bool = False, confirm_response: str = "") -> str:
        """
        Aviat WTM Outdoor Radio does not have a 'save config' command. Instead,
        when changes are detected in config mode, the user is prompted to commit these
        changes. This happens either when trying to exit config mode or when the 'commit'
        command is typed in config mode.
        """
        raise NotImplementedError
