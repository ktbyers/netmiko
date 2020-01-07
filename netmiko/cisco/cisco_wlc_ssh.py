"""Netmiko Cisco WLC support."""
import time
import re

from netmiko.ssh_exception import NetmikoAuthenticationException
from netmiko.base_connection import BaseConnection


class CiscoWlcSSH(BaseConnection):
    """Netmiko Cisco WLC support."""

    def special_login_handler(self, delay_factor=1):
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
                    self.write_channel(self.username + self.RETURN)
                elif "Password" in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1

    def send_command_w_enter(self, *args, **kwargs):
        """
        For 'show run-config' Cisco WLC adds a 'Press Enter to continue...' message
        Even though pagination is disabled
        show run-config also has excessive delays in the output which requires special
        handling.
        Arguments are the same as send_command_timing() method
        """
        if len(args) > 1:
            raise ValueError("Must pass in delay_factor as keyword argument")

        # If no delay_factor use 1 for default value
        delay_factor = kwargs.get("delay_factor", 1)
        kwargs["delay_factor"] = self.select_delay_factor(delay_factor)
        output = self.send_command_timing(*args, **kwargs)

        if "Press any key" in output or "Press Enter to" in output:
            new_args = list(args)
            if len(args) == 1:
                new_args[0] = self.RETURN
            else:
                kwargs["command_string"] = self.RETURN
            if not kwargs.get("max_loops"):
                kwargs["max_loops"] = 150

            # Send an 'enter'
            output = self.send_command_timing(*new_args, **kwargs)

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

    def session_preparation(self):
        """
        Prepare the session after the connection has been established

        Cisco WLC uses "config paging disable" to disable paging
        """
        self._test_channel_read()

        try:
            self.set_base_prompt()
        except ValueError:
            msg = f"Authentication failed: {self.host}"
            raise NetmikoAuthenticationException(msg)

        self.disable_paging(command="config paging disable")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def cleanup(self):
        """Reset WLC back to normal paging."""
        self.send_command_timing("config paging enable")

    def check_config_mode(self, check_string="config", pattern=""):
        """Checks if the device is in configuration mode or not."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super().check_config_mode(check_string, pattern)

    def config_mode(self, config_command="config", pattern=""):
        """Enter into config_mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super().config_mode(config_command, pattern)

    def exit_config_mode(self, exit_config="exit", pattern=""):
        """Exit config_mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super().exit_config_mode(exit_config, pattern)

    def send_config_set(
        self,
        config_commands=None,
        exit_config_mode=False,
        enter_config_mode=False,
        **kwargs,
    ):
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            enter_config_mode=enter_config_mode,
            **kwargs,
        )

    def save_config(self, cmd="save config", confirm=True, confirm_response="y"):
        """Saves Config."""
        self.enable()
        if confirm:
            output = self.send_command_timing(command_string=cmd)
            if confirm_response:
                output += self.send_command_timing(confirm_response)
            else:
                # Send enter by default
                output += self.send_command_timing(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self.send_command(command_string=cmd)
        return output
