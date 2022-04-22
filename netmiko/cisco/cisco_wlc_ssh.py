"""Netmiko Cisco WLC support."""
from typing import Any, Union, Sequence, TextIO
import time
import re
import socket

from netmiko.exceptions import NetmikoAuthenticationException
from netmiko.base_connection import BaseConnection


class CiscoWlcSSH(BaseConnection):
    """Netmiko Cisco WLC support."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # WLC/AireOS has an issue where you can get "No Existing Session" with
        # the default conn_timeout (so increase conn_timeout to 10-seconds).
        kwargs.setdefault("conn_timeout", 10)
        return super().__init__(*args, **kwargs)

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """WLC presents with the following on login (in certain OS versions)

        login as: user

        (Cisco Controller)

        User: user

        Password:****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "login as" in output or "User:" in output:
                    assert isinstance(self.username, str)
                    self.write_channel(self.username + self.RETURN)
                elif "Password" in output:
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                # no output read, sleep and go for one more round of read channel
                time.sleep(delay_factor * 1.5)
            i += 1

    def send_command_w_enter(self, *args: Any, **kwargs: Any) -> str:
        """
        For 'show run-config' Cisco WLC adds a 'Press Enter to continue...' message
        Even though pagination is disabled.

        show run-config also has excessive delays in the output which requires special
        handling.

        Arguments are the same as send_command_timing() method.
        """
        if len(args) > 1:
            raise ValueError("Must pass in delay_factor as keyword argument")

        # If no delay_factor use 1 for default value
        delay_factor = kwargs.get("delay_factor", 1)
        kwargs["delay_factor"] = self.select_delay_factor(delay_factor)
        output = self._send_command_timing_str(*args, **kwargs)

        second_args = list(args)
        if len(args) == 1:
            second_args[0] = self.RETURN
        else:
            kwargs["command_string"] = self.RETURN
        if not kwargs.get("max_loops"):
            kwargs["max_loops"] = 150

        if "Press any key" in output or "Press Enter to" in output:

            # Send an 'enter'
            output += self._send_command_timing_str(*second_args, **kwargs)

            # WLC has excessive delay after this appears on screen
            if "802.11b Advanced Configuration" in output:

                # Defaults to 30 seconds
                time.sleep(kwargs["delay_factor"] * 30)
                not_done = True
                i = 1
                while not_done and i <= 150:
                    time.sleep(kwargs["delay_factor"] * 3)
                    i += 1
                    new_data = ""
                    new_data = self.read_channel()
                    if new_data:
                        output += new_data
                    else:
                        not_done = False

        strip_prompt = kwargs.get("strip_prompt", True)
        if strip_prompt:
            # Had to strip trailing prompt twice.
            output = self.strip_prompt(output)
            output = self.strip_prompt(output)
        return output

    def _send_command_w_yes(self, *args: Any, **kwargs: Any) -> str:
        """
        For 'show interface summary' Cisco WLC adds a
        'Would you like to display the next 15 entries?' message.

        Even though pagination is disabled
        Arguments are the same as send_command_timing() method.
        """
        if len(args) > 1:
            raise ValueError("Must pass in delay_factor as keyword argument")

        # If no delay_factor use 1 for default value
        delay_factor = kwargs.get("delay_factor", 1)
        kwargs["delay_factor"] = self.select_delay_factor(delay_factor)

        output = ""
        new_output = self._send_command_timing_str(*args, **kwargs)

        second_args = list(args)
        if len(args) == 1:
            second_args[0] = "y"
        else:
            kwargs["command_string"] = "y"
        strip_prompt = kwargs.get("strip_prompt", True)

        while True:
            output += new_output
            if "display the next" in new_output.lower():
                new_output = self._send_command_timing_str(*second_args, **kwargs)
            else:
                break

        # Remove from output 'Would you like to display the next 15 entries? (y/n)'
        pattern = r"^.*display the next.*\n$"
        output = re.sub(pattern, "", output, flags=re.M)

        if strip_prompt:
            # Had to strip trailing prompt twice.
            output = self.strip_prompt(output)
            output = self.strip_prompt(output)
        return output

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established

        Cisco WLC uses "config paging disable" to disable paging
        """
        self._test_channel_read(pattern=r"[>#]")

        try:
            self.set_base_prompt()
        except ValueError:
            msg = f"Authentication failed: {self.host}"
            raise NetmikoAuthenticationException(msg)

        self.disable_paging(command="config paging disable")

    def cleanup(self, command: str = "logout") -> None:
        """Reset WLC back to normal paging and gracefully close session."""
        self.send_command_timing("config paging enable")

        # Exit configuration mode
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass

        # End SSH/telnet session
        self.write_channel(command + self.RETURN)
        count = 0
        output = ""
        while count <= 5:
            time.sleep(0.5)

            # The connection might be dead at this point.
            try:
                output += self.read_channel()
            except socket.error:
                break

            # Don't automatically save the config (user's responsibility)
            if "Would you like to save them now" in output:
                self._session_log_fin = True
                self.write_channel("n" + self.RETURN)

            try:
                self.write_channel(self.RETURN)
            except socket.error:
                break
            count += 1

    def check_config_mode(
        self, check_string: str = "config", pattern: str = ""
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super().check_config_mode(check_string, pattern)

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter into config_mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        """Exit config_mode."""
        return super().exit_config_mode(exit_config, pattern)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        enter_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            enter_config_mode=enter_config_mode,
            **kwargs,
        )

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = True,
        confirm_response: str = "y",
    ) -> str:
        """Saves Config."""
        self.enable()
        if confirm:
            output = self._send_command_timing_str(command_string=cmd)
            if confirm_response:
                output += self._send_command_timing_str(confirm_response)
            else:
                # Send enter by default
                output += self._send_command_timing_str(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self._send_command_str(command_string=cmd)
        return output
