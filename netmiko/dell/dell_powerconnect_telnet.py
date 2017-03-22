"""Dell Telnet Driver."""
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection

import time,re

class DellPowerConnectTelnet(CiscoSSHConnection):
    def disable_paging(self, command="terminal length 0", delay_factor=1):
        print ("MADE IT HERE:")
        """Must be in enable mode to disable paging."""
        self.enable()  
        debug = True
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
        TELNET_RETURN = '\r\n'

        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ''
        return_msg = ''
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output):
                    self.write_channel(self.username + TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output):
                    self.write_channel(self.password + TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if pri_prompt_terminator in output or alt_prompt_terminator in output:
                        return return_msg

                # Check if proper data received
                if pri_prompt_terminator in output or alt_prompt_terminator in output:
                    return return_msg

                self.write_channel(TELNET_RETURN)
                time.sleep(.5 * delay_factor)
                i += 1
            except EOFError:
                msg = "Telnet login failed: {0}".format(self.host)
                raise NetMikoAuthenticationException(msg)
