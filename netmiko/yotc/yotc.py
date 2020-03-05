from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from netmiko import log


class YotcBase(CiscoBaseConnection):
    

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
        """Prepare the session after the connection has been established."""

        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
    
    def check_config_mode(self, check_string=")#", pattern="#"):
        """
        Checks if the device is in configuration mode or not.

        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self,
        cmd="wr",
        confirm=True,
        confirm_response="y",
    ):
        """Saves Config."""
        
        self.enable()
        self.exit_config_mode()
        if confirm:
            output = self.send_command_timing(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
            if confirm_response:
                output += self.send_command_timing(
                    confirm_response, strip_prompt=False, strip_command=False, normalize=False
                )
            else:
                # Send enter by default
                output += self.send_command_timing(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self.send_command(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
        return output

    
class YotcSSH(YotcBase):
    
    def special_login_handler(self, delay_factor=1):
        """yotc presents with the following on login (in certain OS versions)

        Password: ***

        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "Password:" in output:
                    self.write_channel(self.secret + self.RETURN)
                    break
                time.sleep(delay_factor * 0.1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 0.1)
            i += 1
    

class YotcTelnet(YotcBase):
    
    pass
    
    
    
