import paramiko
import re
from typing import Optional

from netmiko.no_config import NoConfig
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class FortinetSSH(NoConfig, NoEnable, CiscoSSHConnection):
    prompt_pattern = r"[#$]"

    def _modify_connection_params(self) -> None:
        """Modify connection parameters prior to SSH connection."""
        paramiko_transport = getattr(paramiko, "Transport")
        paramiko_transport._preferred_kex = (
            "diffie-hellman-group14-sha1",
            "diffie-hellman-group-exchange-sha1",
            "diffie-hellman-group-exchange-sha256",
            "diffie-hellman-group1-sha1",
        )

    def _try_session_preparation(self, force_data: bool = False) -> None:
        super()._try_session_preparation(force_data=force_data)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""

        data = self._test_channel_read(pattern=f"to accept|{self.prompt_pattern}")
        # If "set post-login-banner enable" is set it will require you to press 'a'
        # to accept the banner before you login. This will accept if it occurs
        if "to accept" in data:
            self.write_channel("a\r")
            self._test_channel_read(pattern=self.prompt_pattern)

        self.set_base_prompt()
        self._vdoms = self._vdoms_enabled()
        self._os_version = self._determine_os_version()
        # Retain how the 'output mode' was original configured.
        self._original_output_mode = self._get_output_mode()
        self._output_mode = self._original_output_mode
        self.disable_paging()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r"#",
        alt_prompt_terminator: str = r"$",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        if not pattern:
            pattern = self.prompt_pattern
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        if not pattern:
            pattern = self.prompt_pattern
        return super().find_prompt(
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def _vdoms_enabled(self) -> bool:
        """Determine whether virtual domains are enabled or not."""
        check_command = "get system status | grep Virtual"
        output = self._send_command_str(
            check_command, expect_string=self.prompt_pattern
        )
        return bool(
            re.search(r"Virtual domain configuration: (multiple|enable)", output)
        )

    def _config_global(self) -> str:
        """Enter 'config global' mode, raise a ValueError exception on failure."""
        try:
            return self._send_command_str(
                "config global", expect_string=self.prompt_pattern
            )
        except Exception:
            msg = """
Netmiko may require 'config global' access to properly disable output paging.
Alternatively you can try configuring 'configure system console -> set output standard'.
"""
            raise ValueError(msg)

    def _exit_config_global(self) -> str:
        """Exit 'config global' mode."""
        try:
            return self._send_command_str("end", expect_string=self.prompt_pattern)
        except Exception:
            msg = "Unable to properly exit 'config global' mode."
            raise ValueError(msg)

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging is only available with specific roles so it may fail."""

        output = ""
        if self._output_mode == "standard":
            # Do nothing - already correct.
            return ""

        if self._vdoms:
            output += self._config_global()
        disable_paging_commands = [
            "config system console",
            "set output standard",
            "end",
        ]
        output += self.send_multiline(
            disable_paging_commands, expect_string=self.prompt_pattern
        )
        self._output_mode = "standard"

        if self._vdoms:
            output += self._exit_config_global()
        return output

    def _determine_os_version(self) -> str:
        check_command = "get system status | grep Version"
        output = self._send_command_str(
            check_command, expect_string=self.prompt_pattern
        )
        if re.search(r"^Version: .* (v[78]\.).*$", output, flags=re.M):
            return "v7_or_later"
        elif re.search(r"^Version: .* (v[654]\.).*$", output, flags=re.M):
            return "v6_or_earlier"
        else:
            raise ValueError("Unexpected FortiOS Version encountered.")

    def _get_output_mode_v6(self) -> str:
        """
        FortiOS V6 and earlier.
        Retrieve the current output mode.
        """
        if self._vdoms:
            self._config_global()

        output = self._send_command_str("show full-configuration system console")

        if self._vdoms:
            self._exit_config_global()

        pattern = r"^\s+set output (?P<mode>\S+)\s*$"
        result_mode_re = re.search(pattern, output, flags=re.M)
        if result_mode_re:
            result_mode = result_mode_re.group("mode").strip()
            if result_mode in ["more", "standard"]:
                return result_mode

        raise ValueError("Unable to determine the output mode on the Fortinet device.")

    def _get_output_mode_v7(self) -> str:
        """
        FortiOS V7 and later.
        Retrieve the current output mode.
        """
        if self._vdoms:
            self._config_global()

        output = self._send_command_str(
            "get system console", expect_string=self.prompt_pattern
        )

        if self._vdoms:
            self._exit_config_global()

        pattern = r"output\s+:\s+(?P<mode>\S+)\s*$"
        result_mode_re = re.search(pattern, output, flags=re.M)
        if result_mode_re:
            result_mode = result_mode_re.group("mode").strip()
            if result_mode in ["more", "standard"]:
                return result_mode

        raise ValueError("Unable to determine the output mode on the Fortinet device.")

    def _get_output_mode(self) -> str:
        """Save the state of the output mode so it can be reset at the end of the session."""

        # Fortios Version6 does not support 'get system console'
        if "v6" in self._os_version:
            return self._get_output_mode_v6()
        elif "v7" in self._os_version:
            return self._get_output_mode_v7()
        else:
            raise ValueError("Unexpected FortiOS Version encountered.")

    def cleanup(self, command: str = "exit") -> None:
        """Re-enable paging globally."""
        output = ""
        if self._original_output_mode == "more":
            if self._vdoms:
                output += self._config_global()
            commands = [
                "config system console",
                "set output more",
                "end",
            ]
            output += self.send_multiline(commands, expect_string=self.prompt_pattern)
            if self._vdoms:
                self._exit_config_global()
        return super().cleanup(command=command)

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError
