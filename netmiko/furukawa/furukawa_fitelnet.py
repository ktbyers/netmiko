import re
import time
from typing import Any, Optional, Union, Sequence, Iterator, TextIO

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException


class FurukawaFitelnetBase(CiscoBaseConnection):
    """Common methods for Furukawa FITELnet VPN routers.

    FITELnet prompts vary by model:
    - Bare prompts: ">" (user mode), "#" (enable mode)
    - Hostname prompts: "F220>", "F220#", "F220(config)#",
      "F220(config-GigaEthernet1/1)#", etc.

    FITELnet password model:
        - Login password: set via ``username <name> password <pass>`` or
          ``line telnet/console password <pass>``.
        - Enable password: separate from login, set via
          ``enable password <pass>``.
        - The device may show ``<WARNING> weak login password: set the
          password`` messages that contain the word 'password' but are NOT
          actual password prompts.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        # Re-set base prompt after enable (prompt changes from ">" to "#")
        self.set_base_prompt()
        self.disable_paging(command="no more")

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"\#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"(?:user:|username|login|user name)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet/Serial login for FITELnet.

        Overridden because FITELnet shows ``<WARNING>`` messages after login
        that contain the word 'password' (e.g. ``<WARNING> weak login
        password: set the password``).  The base class matches this as a
        password prompt and incorrectly sends the password as a CLI command.

        This override checks for the command prompt **before** checking for
        the password pattern so that warning messages are not confused with
        real password prompts.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output, flags=re.I):
                    self.write_channel(self.username + "\r")
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # FITELnet fix: check for prompt BEFORE password pattern.
                # This prevents matching 'password' in <WARNING> messages.
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                    alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                # Only check for password if no prompt was detected
                if re.search(pwd_pattern, output, flags=re.I):
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + "\r")
                    time.sleep(0.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                        alt_prompt_terminator, output, flags=re.M
                    ):
                        return return_msg

                # Check for device with no password configured
                if re.search(r"assword required, but none set", output):
                    assert self.remote_conn is not None
                    self.remote_conn.close()
                    msg = f"Login failed - Password required, but none set: {self.host}"
                    raise NetmikoAuthenticationException(msg)

                self.write_channel(self.TELNET_RETURN)
                time.sleep(0.5 * delay_factor)
                i += 1

            except EOFError:
                assert self.remote_conn is not None
                self.remote_conn.close()
                msg = f"Login failed: {self.host}"
                raise NetmikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        assert self.remote_conn is not None
        self.remote_conn.close()
        msg = f"Login failed: {self.host}"
        raise NetmikoAuthenticationException(msg)

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode.

        FITELnet uses bare prompts (just ">" or "#"), so we read until
        either prompt character appears rather than relying on base_prompt.
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=r"[>#]")
        return check_string in output

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode on FITELnet.

        Overridden because:
        1. The bare prompt changes from ">" to "#" after enable, causing the
           default ``read_until_prompt()`` to fail.
        2. If the wrong enable password is supplied, the device responds with
           ``<ERROR> Authentication failed`` followed by another ``password:``
           prompt.  The base implementation would hang waiting for "#".
           This override detects the failure immediately.
        """
        output = ""
        if check_state and self.check_enable_mode():
            return output

        self.write_channel(self.normalize_cmd(cmd))
        output += self.read_until_pattern(pattern=rf"(?:{pattern}|#)", re_flags=re_flags)

        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.normalize_cmd(self.secret))
            # Read until "#" (success) or "Authentication failed" (wrong pw).
            output += self.read_until_pattern(pattern=r"(?:#|Authentication failed)")
            if "Authentication failed" in output:
                raise ValueError(
                    "Failed to enter enable mode. The enable password "
                    "(secret) was rejected by the device."
                )

        if not self.check_enable_mode():
            raise ValueError(
                "Failed to enter enable mode. Please ensure you pass "
                "the 'secret' argument to ConnectHandler."
            )
        return output

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """Exit enable mode on FITELnet.

        Overridden because the base implementation uses read_until_prompt()
        which waits for '#', but after 'disable' the prompt changes to '>'.
        """
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_pattern(pattern=r">")
            # Drain any remaining data (serial ports may have buffered echoes)
            time.sleep(0.5)
            self.clear_buffer()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """FITELnet uses a candidate-config model; stay in config mode for commit."""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            **kwargs,
        )

    def commit(
        self,
        read_timeout: float = 120.0,
        comment: str = "",
    ) -> str:
        """
        Commit the candidate configuration on the FITELnet device.

        Applies the working.cfg (candidate) to current.cfg (running).

        commit may prompt with '[y/n]' for confirmation.
        """
        if comment:
            command_string = f"commit comment {comment}"
        else:
            command_string = "commit"

        output = ""
        confirmation = r"onfirm|\[y/[nN]\]"
        pattern = rf"(?:#|{confirmation})"
        new_data = self._send_command_str(
            command_string,
            expect_string=pattern,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

        if re.search(confirmation, new_data):
            output += new_data
            new_data = self._send_command_str(
                "y",
                expect_string=r"#",
                strip_prompt=False,
                strip_command=False,
                read_timeout=read_timeout,
                cmd_verify=False,
            )

        output += new_data

        if "Error" in output or "error" in output or "Failed" in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        return output

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = True,
        confirm_response: str = "y",
    ) -> str:
        """Save working.cfg to boot.cfg (startup configuration).

        FITELnet prompts 'save ok?[y/N]:' by default.
        """
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)

    def strip_command(self, command_string: str, output: str) -> str:
        """Strip command echo from output.

        FITELnet bare prompts cause the echoed command to appear as
        ``#show ...`` instead of ``show ...``, so the base implementation's
        ``output.startswith(cmd)`` check fails.  This override searches for
        the command echo line (optionally prefixed by the prompt character)
        and removes it along with any preceding prompt-only lines.
        """
        cmd = command_string.strip()
        if output.startswith(cmd):
            return super().strip_command(command_string=command_string, output=output)

        output_lines = output.split(self.RESPONSE_RETURN)
        for i, line in enumerate(output_lines):
            line_s = line.strip()
            if line_s == cmd or line_s == f"#{cmd}" or line_s == f">{cmd}":
                start = i + 1
                return self.RESPONSE_RETURN.join(output_lines[start:])
        return output

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output.

        The base implementation only removes a single trailing prompt line.
        FITELnet devices may echo the prompt multiple times (especially on
        serial/telnet), so this override uses a loop to strip all trailing
        empty lines and prompt lines.
        """
        a_string = a_string.rstrip()
        response_list = a_string.split(self.RESPONSE_RETURN)
        base = self.base_prompt.strip()
        valid_prompts = {"#", ">", f"{base}#", f"{base}>"}

        while True:
            if not response_list:
                break
            last_line = response_list[-1].strip()

            # Remove control characters (e.g. BEL \x07) before matching
            clean_line = re.sub(r"[\x00-\x1f\x7f]", "", last_line)

            if clean_line in valid_prompts:
                # Drop the last line
                response_list = response_list[:-1]
                # valid_prompts must now be what we just matched
                valid_prompts = {clean_line}
            else:
                break

        return self.RESPONSE_RETURN.join(response_list)


class FurukawaFitelnetSSH(FurukawaFitelnetBase):
    """Furukawa FITELnet SSH driver."""

    pass


class FurukawaFitelnetTelnet(FurukawaFitelnetBase):
    """Furukawa FITELnet Telnet driver."""

    pass


class FurukawaFitelnetSerial(FurukawaFitelnetBase):
    """Furukawa FITELnet Serial driver.

    serial_login() ultimately calls telnet_login(), so the above telnet_login() code is shared
    between both telnet and serial driver.
    """

    pass
