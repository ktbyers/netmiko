"""Dell Telnet Driver."""
from __future__ import unicode_literals

import time
from netmiko.cisco_base_connection import CiscoBaseConnection


class DellPowerConnectTelnet(CiscoBaseConnection):
    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """Must be in enable mode to disable paging."""
        debug = False

        self.enable()
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        if debug:
            print("In disable_paging")
            print("Command: {}".format(command))
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        if debug:
            print(output)
            print("Exiting disable_paging")
        return output

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"User:", pwd_pattern=r"assword",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        super(DellPowerConnectTelnet, self).telnet_login(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                username_pattern=username_pattern,
                pwd_pattern=pwd_pattern,
                delay_factor=delay_factor,
                max_loops=max_loops)
