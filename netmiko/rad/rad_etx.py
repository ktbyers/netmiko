from __future__ import unicode_literals
from __future__ import print_function
import time
from netmiko.base_connection import BaseConnection


class RadETXBase(BaseConnection):
    """RAD ETX Support, Tested on RAD 203AX, 205A and 220A."""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command='config term length 0')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='admin save', confirm=False, confirm_response=''):
        """Saves Config Using admin save."""
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
        """The Rad ETX software does not have an enable."""
        pass

    def config_mode(self, config_command='config', pattern='>config'):
        """Enter into configuration mode on remote device."""
        return super(RadETXBase, self).config_mode(config_command=config_command,
                                                   pattern=pattern)

    def check_config_mode(self, check_string='>config', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Rad config starts with baseprompt>config.
        """
        return super(RadETXBase, self).check_config_mode(check_string=check_string,
                                                         pattern=pattern)

    def exit_config_mode(self, exit_config='exit all', pattern='#'):
        """Exit from configuration mode."""
        return super(RadETXBase, self).exit_config_mode(exit_config=exit_config,
                                                        pattern=pattern)


class RadETXSSH(RadETXBase):
    """RAD ETX SSH Support.

    Found that a global_delay_factor of 2 is needed at minimum for SSH to the Rad ETX.
    """
    pass


class RadETXTelnet(RadETXBase):
    """RAD ETX Telnet Support."""
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
