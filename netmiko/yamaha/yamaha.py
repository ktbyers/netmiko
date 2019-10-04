from __future__ import print_function
from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection
from netmiko import log
import time
import re


class YamahaBase(BaseConnection):
    def session_preparation(self):
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="console lines infinity")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Yamaha."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Yamaha."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Yamaha."""
        pass

    def check_config_mode(self, check_string="#", pattern=""):
        """Checks if the device is in administrator mode or not."""
        return super(YamahaBase, self).check_config_mode(
            check_string=check_string, pattern=pattern
        )

    def config_mode(self, config_command="administrator", pattern="ssword"):
        """Enter into administrator mode and configure device."""
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            try:
                output += self.read_until_prompt_or_pattern(
                    pattern=pattern
                )
                self.write_channel(self.normalize_cmd(self.secret))
                output += self.read_until_prompt()
            except NetMikoTimeoutException:
                raise ValueError(msg)
            if not self.check_config_mode():
                raise ValueError("Failed to enter administrator mode.")
        return output

    def exit_config_mode(self, exit_config="exit", pattern=">"):
        """Exit from administrator mode.
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            self.write_channel('\n')
            time.sleep(1)
            self.write_channel('\n')
            time.sleep(1)
            output = self.read_channel()
            if '(Y/N)' in output:
                self.write_channel('N')
            self.write_channel('\n')
            time.sleep(1)
            self.write_channel('\n')
            time.sleep(1)
            output += self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug("exit_config_mode: {}".format(output))
        return output

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """Saves Config."""
        self.config_mode()
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


class YamahaSSH(YamahaBase):
    """Yamaha SSH driver."""
    pass


class YamahaTelnet(YamahaBase):
    """Yamaha Telnet driver."""
    pass


