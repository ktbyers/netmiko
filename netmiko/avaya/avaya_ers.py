"""Netmiko support for Avaya Ethernet Routing Switch."""
from __future__ import print_function
from __future__ import unicode_literals

import re
import time
import telnetlib

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoAuthenticationException
from netmiko import log

# Avaya presents Enter Ctrl-Y to begin.
CTRL_Y = "\x19"


class AvayaErsBase(CiscoSSHConnection):
    """Netmiko support for Avaya Ethernet Routing Switch."""
  
    def config_mode(self, config_command='config term', pattern=''):
        """

        Enter into configuration mode on remote device.

        Avaya ERS devices can have a prompt longer than 20 characters in
        config mode.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super(AvayaErsBase, self).config_mode(config_command=config_command,
                                                            pattern=pattern)    
    def check_config_mode(self, check_string='#', pattern=''):
            """

            Checks if the device is in configuration mode or not.
            
            Avaya ERS devices can have a prompt longer than 20 characters in
            config mode.
            """
            if not pattern:
                pattern = re.escape(self.base_prompt)
            return super(AvayaErsBase, self).check_config_mode(check_string=check_string,
                                                                      pattern=pattern)

    def telnet_login(self, pri_prompt_terminator=r'#\s*$', alt_prompt_terminator=r'>\s*$',
                     username_pattern=r"(?:[Uu]ser:|sername|ogin)", pwd_pattern=r"assword",
                     delay_factor=1, max_loops=20):
        """Telnet login. Can be username/password or just password."""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)


        self.sock = self.remote_conn.sock
        self.remote_conn.set_option_negotiation_callback(self._negotiate_echo_on)            

        output = ''
        return_msg = ''
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Handle 'Enter Ctrl-Y to begin / send Ctrl-Y'
                if re.search('Ctrl-Y', output):
                    self.write_channel(CTRL_Y)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                
                # Search for username pattern / send username
                if re.search('Enter Username: ', output):
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search('Enter Password: ', output):
                    self.write_channel(self.password + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for config menu if presented / send 'c' to go to cli
                if re.search('Menu', output):
                    self.write_channel('c')
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if (re.search(pri_prompt_terminator, output, flags=re.M)
                            or re.search(alt_prompt_terminator, output, flags=re.M)):
                        return return_msg                        
                
                # Check if proper data received
                if (re.search(pri_prompt_terminator, output, flags=re.M)
                        or re.search(alt_prompt_terminator, output, flags=re.M)):
                    return return_msg

                #self.write_channel(self.TELNET_RETURN)
                time.sleep(.5 * delay_factor)
                i += 1
            except EOFError:
                msg = "Telnet login failed: {}".format(self.host)
                raise NetMikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if (re.search(pri_prompt_terminator, output, flags=re.M)
                or re.search(alt_prompt_terminator, output, flags=re.M)):
            return return_msg

        msg = "Telnet login failed: {}".format(self.host)
        raise NetMikoAuthenticationException(msg) 

    def special_login_handler(self, delay_factor=1):
        """
        Avaya ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin.

        Some Avaya ERS devices present a menu interface upon login
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Handle 'Enter Ctrl-Y to begin' and Menu if present
        output = ""
        i = 0
        while i <= 6:
            output = self.read_channel()
            if output:
                if 'Ctrl-Y' in output:
                    self.write_channel(CTRL_Y)
                if 'sername' in output:
                    self.write_channel(self.username + self.RETURN)
                if 'ssword' in output:
                    self.write_channel(self.password + self.RETURN)
                if "Menu" in output:
                    self.write_channel('c')
                    break
                time.sleep(.5 * delay_factor)
            else:
                self.write_channel(self.RETURN)
                time.sleep(1 * delay_factor)
            i += 1

    def _negotiate_echo_on(self, sock, cmd, opt):
        # This is supposed to turn server side echoing on and turn other options off.
        if opt == telnetlib.ECHO and cmd in (telnetlib.WILL, telnetlib.WONT):
            self.sock.sendall(telnetlib.IAC + telnetlib.DO + opt)
        elif opt != telnetlib.NOOPT:
            if cmd in (telnetlib.DO, telnetlib.DONT):
                self.sock.sendall(telnetlib.IAC + telnetlib.WONT + opt)
            elif cmd in (telnetlib.WILL, telnetlib.WONT):
                self.sock.sendall(telnetlib.IAC + telnetlib.DONT + opt)            

class AvayaErsSSH(AvayaErsBase):
    pass

class AvayaErsTelnet(AvayaErsBase):
    pass



