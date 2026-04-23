import re
import time
from typing import Optional

from netmiko.cisco_base_connection import CiscoBaseConnection


class FurukawaFitelnetBase(CiscoBaseConnection):
    """Common methods for Furukawa FITELnet VPN routers.

    FITELnet prompts vary by model:
    - Bare prompts: ">" (user mode), "#" (enable mode)
    - Hostname prompts: "F220>", "F220#", "F220(config)#",
      "F220(config-GigaEthernet1/1)#", etc.
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
        pwd_pattern: str = r"assword:\s*$",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet/Serial login for FITELnet.

        FITELnet emits ``<WARNING> weak login password: set the password``
        right after login.  The base class default ``pwd_pattern = r"assword"``
        matches the word 'password' inside that warning and incorrectly sends
        the password as a CLI command.  Anchoring to ``assword:\\s*$`` limits
        matches to a real ``password:`` prompt at end-of-line.
        """
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode.

        FITELnet uses bare prompts (just ">" or "#"), so we match the
        prompt character at end-of-line to avoid false matches on
        ``<WARNING>`` / ``<ERROR>`` messages that contain ``>``.
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=r"[>#]\s*$")
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

        ``enable_pattern`` is accepted for API compatibility with the parent
        signature but is not used; this override hardcodes the success /
        failure detection patterns.
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
            output += self.read_until_pattern(pattern=r">\s*$")
            # Drain any remaining data (serial ports may have buffered echoes)
            time.sleep(0.5)
            self.clear_buffer()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def commit(
        self,
        read_timeout: float = 120.0,
    ) -> str:
        """
        Commit the candidate configuration on the FITELnet device.

        Applies the working.cfg (candidate) to current.cfg (running).

        commit may prompt with '[y/n]' for confirmation.
        """
        output = ""
        confirmation = r"onfirm|\[y/[nN]\]"
        pattern = rf"(?:#|{confirmation})"
        new_data = self._send_command_str(
            "commit",
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

        # FITELnet refuses commit while another session/process is active with
        # "Another processing is executing. This command can not be executed."
        # The message contains neither "error" nor "failed", so it must be
        # detected separately before the generic error check below.
        if "Another processing is executing" in output:
            raise ValueError(
                "Commit failed: another process is executing on the device. "
                "Retry once the other operation completes."
            )

        # FITELnet emits <ERROR> in all caps; match case-insensitively.
        if re.search(r"error|failed", output, re.IGNORECASE):
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

        If another process is holding the config (e.g. a concurrent session
        in the middle of commit/save/refresh), FITELnet replies with
        "Another processing is executing. This command can not be executed."
        and never prints the ``[y/N]`` prompt — so the confirm_response would
        then be sent as a bare CLI command.  Detect this explicitly and raise.
        """
        output = super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)
        if "Another processing is executing" in output:
            raise ValueError(
                "save_config failed: another process is executing on the device. "
                "Retry once the other operation completes."
            )
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
