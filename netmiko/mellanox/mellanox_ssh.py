
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log
import time


class MellanoxSSH(CiscoSSHConnection):

    def config_mode(self, config_command='config term', pattern='#'):
        """Enter into config_mode."""
        output = ''
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def check_config_mode(self, check_string='(config)', pattern=r'[>|#]'):
        return super(MellanoxSSH, self).check_config_mode(check_string=check_string,
                                                          pattern=pattern)

    def disable_paging(self, command="terminal length 999", delay_factor=1):
        """Disable paging default to a Cisco CLI method."""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("In disable_paging")
        log.debug("Command: {0}".format(command))
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        log.debug("{0}".format(output))
        log.debug("Exiting disable_paging")
        return output

    def exit_config_mode(self, exit_config='exit', pattern='#'):
        """Exit from configuration mode."""
        output = ''
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            output = self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug("exit_config_mode: {0}".format(output))
        return output

    def save_config(self, cmd='configuration write', confirm=False,
                    confirm_response=''):
        """Save Config on Mellanox devices Enters and Leaves Config Mode"""
        output = self.enable()
        output += self.config_mode()
        output += self.send_command(cmd)
        output += self.exit_config_mode()
        return output
