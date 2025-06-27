import re

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException


class HiosoBase(CiscoBaseConnection):
    prompt_pattern = r"[\]>]"
    password_change_prompt = r"(?:Change now|Please choose)"
    prompt_or_password_change = rf"(?:Change now|Please choose|{prompt_pattern})"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # The _test_channel_read happens in special_login_handler()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0")
        self.find_prompt()  # The disable_paging doesn't clear the buffer
        self.exit_enable_mode(exit_command="exit")

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(
            self,
            exit_config: str = "exit",
            pattern: str = r"#"
    ) -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(
            exit_config=exit_config, pattern=pattern
        )

    def check_config_mode(
        self,
        check_string: str = ")",
        pattern: str = "",
        force_regex: bool = False
    ) -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string)

    def save_config(
        self,
        cmd: str = "write file",
        confirm: bool = False,
        confirm_response: str = "y"
    ) -> str:
        """Save Config for Hioso Telnet."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def cleanup(self, command: str = "quit") -> None:
        return super().cleanup(command=command)


class HiosoTelnet(HiosoBase):
    """Hioso Telnet driver."""

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"",
        alt_prompt_terminator: str = r"",
        username_pattern: str = r"(?:user:|username|login|user name)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet login for Huawei Devices"""
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

            # Wait for the prompt
            if re.search(self.prompt_pattern, output):
                return return_msg

            # Should never be here
            raise EOFError

        except EOFError:
            assert self.remote_conn is not None
            self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)
