"""Subclass specific to Cisco FTD."""

from typing import Any, Optional
import re
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(NoConfig, CiscoSSHConnection):
    """Subclass specific to Cisco FTD.

    FTD has two CLI layers:

    1. FTD CLI (top level) - where you land after SSH login.
       Prompt: firepower>
       No enable mode; no config mode.

    2. Diagnostic CLI (ASA sub-shell) - entered via
        firepower> system support diagnostic-cli
        Attaching to Diagnostic CLI ...
        Type help or '?' for a list of available commands.

        firepower> enable
        Password:             <-- Press Enter here (no password)
        firepower#

    Calling enable() enters the diagnostic CLI and elevates to '#'.
    Calling exit_enable_mode() returns to the top-level FTD CLI.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode (diagnostic CLI privileged exec)."""
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "system support diagnostic-cli",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = r"\#",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode on FTD via the diagnostic CLI.

        Sends 'system support diagnostic-cli' to enter the ASA/Lina
        sub-shell, then runs 'enable' if still at user-exec prompt ('>').
        The diagnostic CLI enable password is always empty (always send
        null-string).
        """
        output = ""
        if check_state and self.check_enable_mode():
            return output

        # Enter the diagnostic CLI
        self.write_channel(self.normalize_cmd(cmd))
        if self.global_cmd_verify is not False:
            output += self.read_until_pattern(pattern=re.escape(cmd.strip()))
        output += self.read_until_pattern(pattern=r"[>#]")

        # Track that we are inside the diagnostic CLI so exit_enable_mode
        # knows to send a second 'exit' to return to the FTD CLI.
        self._in_diagnostic_cli = True

        # If at user-exec mode ('>'), elevate to enable ('#')
        last_line = output.splitlines()[-1] if output.strip() else ""
        if re.search(r">\s*$", last_line):
            output += super().enable(
                cmd="enable",
                pattern=pattern,
                enable_pattern=enable_pattern,
                check_state=False,
                re_flags=re_flags,
            )

        self.set_base_prompt()
        return output

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit diagnostic CLI and return to the top-level FTD CLI.

        Uses Ctrl+a, d to detach from the diagnostic CLI process,
        returning directly to the FTD CLI regardless of current
        privilege level (> or #).
        """
        output = ""
        if getattr(self, "_in_diagnostic_cli", False):
            output += self._send_command_str("\x01d", expect_string=r">", cmd_verify=False)
            self._in_diagnostic_cli = False
            self.set_base_prompt()
        return output

    def send_config_set(self, *args: Any, **kwargs: Any) -> str:
        """Cannot change config on FTD via SSH."""
        raise NotImplementedError

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Cannot change config on FTD via SSH."""
        return False
