from __future__ import unicode_literals
import time
import re
from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.cisco_base_connection import CiscoBaseConnection


class IpinfusionOcnosBase(CiscoBaseConnection):
    """Common Methods for IP Infusion OcNOS support."""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")

        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='write', confirm=False, confirm_response=''):
        """Saves Config Using write command"""
        return super(IpinfusionOcnosBase, self).save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response)

    def enable(self, cmd='enable', pattern='ssword', re_flags=re.IGNORECASE):
        """Enter enable mode.

        :param cmd: Device command to enter enable mode
        :type cmd: str

        :param pattern: pattern to search for indicating device is waiting for password
        :type pattern: str

        :param re_flags: Regular expression flags used in conjunction with pattern
        :type re_flags: int
        """
        output = ""
        msg = "Failed to enter enable mode. Please ensure you pass " \
              "the 'secret' argument to ConnectHandler."
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            try:
                output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
                self.write_channel(self.secret + self.TELNET_RETURN)
                output += self.read_until_prompt()
            except NetMikoTimeoutException:
                raise ValueError(msg)
            if not self.check_enable_mode():
                raise ValueError(msg)
        return output


class IpinfusionOcnosSSH(IpinfusionOcnosBase):
    """IP Infusion OcNOS SSH driver."""
    pass


class IpinfusionOcNOSTelnet(IpinfusionOcnosBase):
    """IP Infusion OcNOS  Telnet driver."""

    """
    For all telnet options, re-implement the default telnetlib behaviour
    and refuse to handle any options. If the server expresses interest in
    'terminal type' option, then reply back with 'xterm' terminal type.
    """
    def process_option(self, tsocket, command, option):
        if command == DO and option == TTYPE:
            tsocket.sendall(IAC + WILL + TTYPE)
            tsocket.sendall(IAC + SB + TTYPE + b'\0' + b'xterm' + IAC + SE)
        elif command in (DO, DONT):
            tsocket.sendall(IAC + WONT + option)
        elif command in (WILL, WONT):
            tsocket.sendall(IAC + DONT + option)

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"(?:user:|sername|login|user name)", pwd_pattern=r"assword:",
                     delay_factor=1, max_loops=20):
        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self.process_option)
        return super(IpinfusionOcNOSTelnet, self).telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern, pwd_pattern=pwd_pattern,
            delay_factor=delay_factor, max_loops=max_loops)
