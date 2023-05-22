import re
import time
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.dsa import DSAParameterNumbers

from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import ReadTimeout


class TPLinkJetStreamBase(CiscoSSHConnection):
    def __init__(self, **kwargs: Any) -> None:
        # TP-Link doesn't have a way to set terminal width which breaks cmd_verify
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        # TP-Link uses "\r\n" as default_enter for SSH and Telnet
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(0.3 * delay_factor)
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(
        self,
        cmd: str = "",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        TPLink JetStream requires you to first execute "enable" and then execute "enable-admin".
        This is necessary as "configure" is generally only available at "enable-admin" level

        If the user does not have the Admin role, he will need to execute enable-admin to really
        enable all functions.
        """

        msg = """
Failed to enter enable mode. Please ensure you pass
the 'secret' argument to ConnectHandler.
"""

        # If end-user passes in "cmd" execute that using normal process.
        if cmd:
            return super().enable(
                cmd=cmd,
                pattern=pattern,
                enable_pattern=enable_pattern,
                check_state=check_state,
                re_flags=re_flags,
            )

        output = ""
        if check_state and self.check_enable_mode():
            return output

        for cmd in ("enable", "enable-admin"):
            self.write_channel(self.normalize_cmd(cmd))
            try:
                new_data = self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags, read_entire_line=True
                )
                output += new_data
                if re.search(pattern, new_data):
                    self.write_channel(self.normalize_cmd(self.secret))
                    output += self.read_until_prompt(read_entire_line=True)
            except ReadTimeout:
                raise ValueError(msg)

        if not self.check_enable_mode():
            raise ValueError(msg)
        return output

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#") -> str:
        """
        Exit config mode.

        Like the Mellanox equipment, the TP-Link Jetstream does not
        support a single command to completely exit the configuration mode.

        Consequently, need to keep checking and sending "exit".
        """
        output = ""
        check_count = 12
        while check_count >= 0:
            if self.check_config_mode():
                self.write_channel(self.normalize_cmd(exit_config))
                output += self.read_until_pattern(pattern=pattern)
            else:
                break
            check_count -= 1

        if self.check_config_mode():
            raise ValueError("Failed to exit configuration mode")
            log.debug(f"exit_config_mode: {output}")

        return output

    def check_config_mode(
        self,
        check_string: str = "(config",
        pattern: str = r"#",
        force_regex: bool = False,
    ) -> bool:
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple
        contexts. For TP-Link this will be the router prompt with > or #
        stripped off.

        This will be set on logging in, but not when entering system-view
        """
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )


class TPLinkJetStreamSSH(TPLinkJetStreamBase):
    def __init__(self, **kwargs: Any) -> None:
        setattr(dsa, "_check_dsa_parameters", self._override_check_dsa_parameters)
        return super().__init__(**kwargs)

    def _override_check_dsa_parameters(self, parameters: DSAParameterNumbers) -> None:
        """
        Override check_dsa_parameters from cryptography's dsa.py

        Without this the error below occurs:

        ValueError: p must be exactly 1024, 2048, or 3072 bits long

        Allows for shorter or longer parameters.p to be returned
        from the server's host key. This is a HORRIBLE hack and a
        security risk, please remove if possible!

        By now, with firmware:

        2.0.5 Build 20200109 Rel.36203(s)

        It's still not possible to remove this hack.
        """
        if parameters.q.bit_length() not in [160, 256]:
            raise ValueError("q must be exactly 160 or 256 bits long")

        if not (1 < parameters.g < parameters.p):
            raise ValueError("g, p don't satisfy 1 < g < p.")


class TPLinkJetStreamTelnet(TPLinkJetStreamBase):
    def telnet_login(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        username_pattern: str = r"User:",
        pwd_pattern: str = r"Password:",
        delay_factor: float = 1.0,
        max_loops: int = 60,
    ) -> str:
        """Telnet login: can be username/password or just password."""
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
