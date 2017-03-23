from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class AristaSSH(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Arista, unfortunately, does this:
        loc1-core01(s1)#

        Can also be (s2)
        """
        debug = False
        if debug:
            print("pattern: {}".format(pattern))
        self.write_channel('\n')
        output = self.read_until_pattern(pattern=pattern)
        if debug:
            print("check_config_mode: {}".format(repr(output)))
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        if debug:
            print("check_config_mode: {}".format(repr(output)))
        return check_string in output
