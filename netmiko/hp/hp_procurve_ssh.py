from __future__ import print_function
from __future__ import unicode_literals
import re
import time
import socket
from netmiko.cisco_base_connection import CiscoSSHConnection


class HPProcurveSSH(CiscoSSHConnection):

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Procurve uses - 'Press any key to continue'
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(2 * delay_factor)
        self.write_channel("\n")
        time.sleep(2 * delay_factor)
        self.write_channel("\n")
        time.sleep(2 * delay_factor)

        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        self.set_base_prompt()
        self.disable_paging(command="\nno page\n")
        self.set_terminal_width(command='terminal width 511')

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE,
               default_username='manager'):
        """Enter enable mode"""
        debug = False
        output = self.send_command_timing(cmd)
        if 'username' in output.lower():
            output += self.send_command_timing(default_username)
        if 'password' in output.lower():
            output += self.send_command_timing(self.secret)
        if debug:
            print(output)
        self.clear_buffer()
        return output

    def cleanup(self):
        """Gracefully exit the SSH session."""
        self.exit_config_mode()
        self.write_channel("logout\n")
        count = 0
        while count <= 5:
            time.sleep(.5)
            output = self.read_channel()
            if 'Do you want to log out' in output:
                self.write_channel("y\n")
            # Don't automatically save the config (user's responsibility)
            elif 'Do you want to save the current' in output:
                self.write_channel("n\n")
            try:
                self.write_channel("\n")
            except socket.error:
                break
            count += 1
