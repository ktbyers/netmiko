import re
from typing import Optional

from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException


class HuaweiONTBase(NoConfig, CiscoBaseConnection):
    prompt_pattern = r"WAP>"
    su_prompt_pattern = r"SU_WAP>"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # The _test_channel_read happens in special_login_handler()
        self.set_base_prompt()

    def save_config(
        self, cmd: str = "save", confirm: bool = True, confirm_response: str = "y"
    ) -> str:
        """In Huawei ONTs, there is no save command. All changes are immediate."""
        raise NotImplementedError("Save config is not supported on Huawei ONTs.")

    def check_enable_mode(self, check_string: str = r"SU_WAP\>") -> bool:
        """Check if the device is in su mode."""
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "su",
        pattern: str = "",
        enable_pattern: Optional[str] = r"WAP\>",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Attempt to become super user."""
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def exit_enable_mode(self, exit_command: str = "quit") -> str:
        """Exit super user mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def cleanup(self, command: str = "logout") -> None:
        """Attempt to logout."""
        return super().cleanup(command=command)


class HuaweiONTSSH(HuaweiONTBase):
    """Huawei SSH driver."""

    pass


class HuaweiONTTelnet(HuaweiONTBase):
    """Huawei Telnet driver."""

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"",
        alt_prompt_terminator: str = r"",
        username_pattern: str = r"(?:user:|username|login|Login|user name)",
        pwd_pattern: str = r"Password:|password:",
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

            output = self.read_until_pattern(pattern=self.prompt_pattern)
            # Wait for prompt_pattern
            if re.search(self.prompt_pattern, output):
                return return_msg

            # Should never be here
            raise EOFError

        except EOFError:
            assert self.remote_conn is not None
            self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)
