from __future__ import unicode_literals
from __future__ import print_function
import time
from netmiko.base_connection import BaseConnection

class RadETXBase(BaseConnection):
    """RAD ETX Support, Tested on RAD 203AX, 205A and 220A"""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="config term length 0")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='admin save', confirm=False, confirm_response=''):
        """Saves Config Using admin save"""
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
    
    def enable(self, *args, **kwargs):
        pass

class RadETXSSH(RadETXBase):
    """RAD ETX SSH Support"""
    pass

class RadETXTelnet(RadETXBase):
    """RAD ETX Telnet Support"""
    def telnet_login(self, delay_factor=1):
        """
        RAD presents with the following on login

        user>

        password> ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * .5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if 'user>' in output:
                    self.write_channel(self.username + self.RETURN)
                elif 'password>' in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1
