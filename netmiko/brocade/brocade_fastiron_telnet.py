from __future__ import unicode_literals
import re
from netmiko.cisco_base_connection import CiscoBaseConnection


class BrocadeFastironTelnet(CiscoBaseConnection):
    """Brocade FastIron aka ICX support."""
    def session_preparation(self):
        """FastIron requires to be enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n\r\n', '\r\r\n','\r\n', '\n\r' to '\n."""
        newline = re.compile(r'(\r\n\r\n|\r\r\n|\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"Username:", pwd_pattern=r"assword:",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        super(BrocadeFastironTelnet, self).telnet_login(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                username_pattern=username_pattern,
                pwd_pattern=pwd_pattern,
                delay_factor=delay_factor,
                max_loops=max_loops)

    def _test_channel_read(self, count=40, pattern="", newline_format="\r"):
        super(BrocadeFastironTelnet, self)._test_channel_read(count=count,
                                                              pattern=pattern,
                                                              newline_format=newline_format)

    def find_prompt(self, delay_factor=1, newline_format="\r"):
        return super(BrocadeFastironTelnet, self).find_prompt(delay_factor=delay_factor,
                                                              newline_format=newline_format)

    @staticmethod
    def normalize_cmd(command, newline_format="\r"):
        return super(BrocadeFastironTelnet,
                     BrocadeFastironTelnet).normalize_cmd(command,
                                                          newline_format=newline_format)

    def check_enable_mode(self, check_string='', newline_format="\r"):
        return super(BrocadeFastironTelnet, self).check_enable_mode(check_string=check_string,
                                                                    newline_format=newline_format)

    def check_config_mode(self, check_string=')#', pattern='', newline_format="\r"):
        return super(BrocadeFastironTelnet, self).check_config_mode(check_string=check_string,
                                                                    pattern=pattern,
                                                                    newline_format=newline_format)
