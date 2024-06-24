import re
import time
from socket import socket
from typing import Optional, Any

from netmiko._telnetlib.telnetlib import DO, DONT, ECHO, IAC, WILL, WONT, Telnet
from netmiko.cisco_base_connection import CiscoSSHConnection


class RuckusFastironBase(CiscoSSHConnection):
    """Ruckus FastIron aka ICX support."""

    def session_preparation(self) -> None:
        """FastIron requires to be enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = r"(ssword|User Name|Login)",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode.
        With RADIUS can prompt for User Name or Login
        SSH@Lab-ICX7250>en
        User Name:service_netmiko
        Password:
        SSH@Lab-ICX7250#
        """
        output = ""
        if check_state and self.check_enable_mode():
            return output

        count = 4
        i = 1
        while i < count:
            self.write_channel(self.normalize_cmd(cmd))
            new_data = self.read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags, read_entire_line=True
            )
            output += new_data
            if "User Name" in new_data or "Login" in new_data:
                self.write_channel(self.normalize_cmd(self.username))
                new_data = self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags, read_entire_line=True
                )
                output += new_data
            if "ssword" in new_data:
                self.write_channel(self.normalize_cmd(self.secret))
                new_data = self.read_until_prompt(read_entire_line=True)
                output += new_data
                if not re.search(r"error.*incorrect.*password", new_data, flags=re.I):
                    break

            time.sleep(1)
            i += 1

        if not self.check_enable_mode():
            msg = (
                "Failed to enter enable mode. Please ensure you pass "
                "the 'secret' argument to ConnectHandler."
            )
            raise ValueError(msg)

        return output

    def save_config(
        self, cmd: str = "write mem", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class RuckusFastironTelnet(RuckusFastironBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def _process_option(self, tsocket: socket, command: bytes, option: bytes) -> None:
        """
        Ruckus FastIron/ICX does not always echo commands to output by default.
        If server expresses interest in 'ECHO' option, then reply back with 'DO
        ECHO'
        """
        if option == ECHO:
            tsocket.sendall(IAC + DO + ECHO)
        elif command in (DO, DONT):
            tsocket.sendall(IAC + WONT + option)
        elif command in (WILL, WONT):
            tsocket.sendall(IAC + DONT + option)

    def telnet_login(self, *args: Any, **kwargs: Any) -> str:
        # set callback function to handle telnet options.
        assert isinstance(self.remote_conn, Telnet)
        self.remote_conn.set_option_negotiation_callback(self._process_option)  # type: ignore
        return super().telnet_login(*args, **kwargs)


class RuckusFastironSSH(RuckusFastironBase):
    pass
