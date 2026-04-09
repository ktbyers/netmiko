import re

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException


class HiosoOLTBase(CiscoBaseConnection):
    """
    Base class for Hioso OLT devices.
    It is fairly similar to Cisco devices.
    """

    prompt_pattern = r"[#>]"
    prompt_or_password_change = rf"(?:Change now|Please choose|{prompt_pattern})"

    def session_preparation(self) -> None:
        """Prepare the session after the connection is established."""
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        self.clear_buffer()
        self.exit_enable_mode()

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#") -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self,
        cmd: str = "write file",
        confirm: bool = False,
        confirm_response: str = "y",
    ) -> str:
        """Save Config for Hioso OLT."""
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)

    def cleanup(self, command: str = "quit") -> None:
        """Cleanup the connection."""
        super().cleanup(command=command)


class HiosoOLTTelnet(HiosoOLTBase):
    """Hioso OLT Telnet driver."""

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"",
        alt_prompt_terminator: str = r"",
        username_pattern: str = r"(?:user:|username|login|user name)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet login for Hioso OLT devices."""
        output = ""
        return_msg = ""
        try:
            # Search for username pattern / send username
            output = self.read_until_pattern(pattern=username_pattern, re_flags=re.I)
            return_msg += output
            self.write_channel(self.username + self.TELNET_RETURN)

            # Search for password pattern / send password
            output = self.read_until_pattern(pattern=pwd_pattern, re_flags=re.I)
            return_msg += output
            assert self.password is not None
            self.write_channel(self.password + self.TELNET_RETURN)

            # Waiting for the prompt or password change message
            output = self.read_until_pattern(pattern=self.prompt_or_password_change)
            return_msg += output

            # "Welcome to Hioso OLT. Please choose the management mode
            #  (1: CLI, 2: Web Management Selection):" — send "1" for CLI
            if re.search(r"Please choose", output):
                self.write_channel("1" + self.TELNET_RETURN)
                output = self.read_until_pattern(pattern=self.prompt_or_password_change)
                return_msg += output

            # "The current password is the default password. It is recommended
            #  to change it for security. Change now? [Y/N]" — send "N" to skip
            if re.search(r"Change now", output):
                self.write_channel("N" + self.TELNET_RETURN)
                output = self.read_until_pattern(pattern=self.prompt_pattern)
                return_msg += output

            # Wait for the prompt
            if re.search(self.prompt_pattern, output):
                return return_msg

            # Should never be here
            raise EOFError

        except EOFError:
            if self.remote_conn is not None:
                self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)
