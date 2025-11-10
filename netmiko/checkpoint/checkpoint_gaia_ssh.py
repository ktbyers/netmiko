import time
import re
from typing import Optional

from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection
from netmiko.exceptions import ReadTimeout


class CheckPointGaiaSSH(NoConfig, BaseConnection):
    """
    Implements methods for communicating with Check Point Gaia
    firewalls.
    """

    prompt_pattern = r"[>#]"

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('>').
        """
        # Kept running into issues with command_echo and duplicate
        # echoes of commands.
        self.fast_cli = False
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="set clienv rows 0")

        # Clear read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable_secret_handler(
        self,
        pattern: str,
        output: str
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        Check Point Gaia requires very particular timing for this 'expert'
        password handling to work.

        Send the "secret" in response to password pattern
        """
        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.secret))
            print(output)
            time.sleep(.3)
            self.write_channel("\n")
            time.sleep(.3)
            output += self.read_until_pattern(pattern=r"[>#]")
            #print(self.read_channel())
#2060                 #output += self.read_until_prompt()
#2061                 print(output)
#2062                 time.sleep(.3)
#2063                 self.write_channel("\n")
#2064                 time.sleep(.3)
#2065                 #print(self.read_channel())
#2066                 output += self.read_until_pattern(pattern=r"[>#]")

    def enable(
        self,
        cmd: str = "expert",
        pattern: str = r"expert password",
        enable_pattern: Optional[str] = r"\#",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        Enter expert mode.

        Check Point Gaia is very finicky on the timing of sending this 'expert' password.
        """
        output = super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )
        self.set_base_prompt()
        return output

        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )

        # Check if in enable mode already.
        if check_state and self.check_enable_mode():
            return output

        # Send "enable" mode command
        self.write_channel(self.normalize_cmd(cmd))
        try:
            # Read the command echo
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

            # Gaia is really tricky as it frequently double echoes the cmd
            try:
                tmp_pattern = rf"(?:>\s{re.escape(cmd.strip())}|{pattern})"
                output += self.read_until_pattern(pattern=tmp_pattern, read_timeout=3)
            except ReadTimeout:
                # No double echo / no prompt to enter password (give up).
                raise ValueError(msg)

            print(output)

            # Must have hit double echo
            if not re.search(pattern, output):
                time.sleep(.3)
                # Search for trailing prompt or password pattern
                output += self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags, read_entire_line=True
                )

            print(output)

            # Send the "secret" in response to password pattern
            if re.search(pattern, output, flags=re_flags):
                self.write_channel(self.secret)
                time.sleep(.5)
                self.write_channel("\r")

            # Search for terminating pattern if defined
            if enable_pattern:
                output += self.read_until_pattern(pattern=enable_pattern)
            else:
                output += self.read_until_prompt()
                if not self.check_enable_mode():
                    raise ValueError(msg)

        except NetmikoTimeoutException:
            raise ValueError(msg)

        print(output)
        self.set_base_prompt()
        return output

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exits enable (privileged exec) mode."""
        output = super().exit_enable_mode(exit_command=exit_command)
        self.set_base_prompt()
        return output

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        raise NotImplementedError
