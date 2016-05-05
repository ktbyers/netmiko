"""Netmiko Cisco WLC support."""
from __future__ import print_function
from __future__ import unicode_literals
import time

from netmiko.ssh_connection import BaseSSHConnection
from netmiko.netmiko_globals import MAX_BUFFER


class CiscoWlcSSH(BaseSSHConnection):
    """Netmiko Cisco WLC support."""

    def special_login_handler(self, delay_factor=1):
        '''
        WLC presents with the following on login (in certain OS versions)

        login as: user

        (Cisco Controller)

        User: user

        Password:****
        '''
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * .5)
        while i <= 12:
            if self.remote_conn.recv_ready():
                output = self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if 'login as' in output or 'User' in output:
                    self.remote_conn.sendall(self.username + '\n')
                elif 'Password' in output:
                    self.remote_conn.sendall(self.password + '\n')
                    break
                time.sleep(delay_factor * 1)
            else:
                self.remote_conn.sendall('\n')
                time.sleep(delay_factor * 1.5)
            i += 1

    def send_command_w_enter(self, *args, **kwargs):
        '''
        For 'show run-config' Cisco WLC adds a 'Press Enter to continue...' message
        Even though pagination is disabled
        show run-config also has excessive delays in the output which requires special
        handling.
        Arguments are the same as send_command() method
        '''
        if len(args) > 1:
            raise ValueError("Must pass in delay_factor as keyword argument")

        # If no delay_factor use 3 for default value (unless global_delay_factor is greater)
        if kwargs.get('delay_factor'):
            kwargs['delay_factor'] = self.select_delay_factor(kwargs['delay_factor'])
        else:
            kwargs['delay_factor'] = self.select_delay_factor(3)
        output = self.send_command(*args, **kwargs)

        if 'Press Enter to' in output:
            new_args = list(args)
            if len(args) == 1:
                new_args[0] = '\n'
            else:
                kwargs['command_string'] = '\n'
            if not kwargs.get('max_loops'):
                kwargs['max_loops'] = 150

            # Send an 'enter'
            output = self.send_command(*new_args, **kwargs)

            # WLC has excessive delay after this appears on screen
            if '802.11b Advanced Configuration' in output:

                # Defaults to 30 seconds
                time.sleep(kwargs['delay_factor'] * 10)
                not_done = True
                i = 1
                while (not_done) and (i <= 150):
                    time.sleep(kwargs['delay_factor'])
                    i += 1
                    if self.remote_conn.recv_ready():
                        # Unicode error occurred in output (errors=ignore strips this out).
                        output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                    else:
                        not_done = False

        strip_prompt = kwargs.get('strip_prompt', True)
        if strip_prompt:
            # Had to strip trailing prompt twice.
            output = self.strip_prompt(output)
            output = self.strip_prompt(output)
        return output

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        Cisco WLC uses "config paging disable" to disable paging
        '''
        self.set_base_prompt()
        self.disable_paging(command="config paging disable\n")

    def cleanup(self):
        """Reset WLC back to normal paging."""
        self.send_command("config paging enable\n")
