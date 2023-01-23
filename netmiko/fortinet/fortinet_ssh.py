import paramiko
import re
from typing import Optional

from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class FortinetSSH(NoConfig, CiscoSSHConnection):
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

        self.set_base_prompt(alt_prompt_terminator="$")
        self.disable_paging()

        self._vdoms = self._vdoms_enabled()
        self._output_mode = "unknown"

    def _vdoms_enabled(self) -> bool:
        """Determine whether virtual domains are enabled or not."""
        check_command = "get system status | grep Virtual"
        output = self._send_command_str(
            check_command, expect_string=self.prompt_pattern
        )
        return bool(
            re.search(r"Virtual domain configuration: (multiple|enable)", output)
        )

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging is only available with specific roles so it may fail."""

        if self._output_mode == "unknown":
            # Save the state of output paging
            self._retrieve_output_mode()

        if self._output_mode == "standard":
            # Do nothing - already correct.
            return ""

        if self._vdoms:
            vdom_additional_command = "config global"
            try:
                output = self._send_command_str(
                    vdom_additional_command, expect_string=self.prompt_pattern
                )
            except Exception:
                msg = """
Netmiko requires 'config global' access to properly disable output paging
(when VDOMs are enabled). Alternatively you can configure 'set output standard'
and Netmiko should detect this.
"""
                raise ValueError(msg)

        disable_paging_commands = [
            "config system console",
            "set output standard",
            "end",
        ]
        # There is an extra 'end' required if in multi-vdoms are enabled
        if self._vdoms:
            disable_paging_commands.append("end")
        output += self.send_multiline(
            disable_paging_commands, expect_string=self.prompt_pattern
        )
        return output

    def _retrieve_output_mode(self) -> None:
        """Save the state of the output mode so it can be reset at the end of the session."""
        pattern = r"output\s+:\s+(?P<mode>.*)\s+\n"
        output = self._send_command_str(
            "get system console", expect_string=self.prompt_pattern
        )
        result_mode_re = re.search(pattern, output)
        if result_mode_re:
            result_mode = result_mode_re.group("mode").strip()
            if result_mode in ["more", "standard"]:
                self._output_mode = result_mode
            else:
                raise ValueError(
                    "Unable to determine the output mode on the Fortinet device."
                )

    def cleanup(self, command: str = "exit") -> None:
        """Re-enable paging globally."""
        output = ""
        if self._output_mode == "more":
            commands = []
            if self._vdoms:
                commands = ["config global"]
            commands += [
                "config system console",
                "set output more",
                "end",
            ]
            output += self.send_multiline(commands, expect_string=self.prompt_pattern)
        return super().cleanup(command=command)

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError
