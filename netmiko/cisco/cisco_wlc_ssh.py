"""Netmiko Cisco WLC support."""
from __future__ import print_function
from __future__ import unicode_literals
import time

from netmiko.base_connection import BaseConnection


class CiscoWlcSSH(BaseConnection):
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
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if 'login as' in output or 'User' in output:
                    self.write_channel(self.username + '\n')
                elif 'Password' in output:
                    self.write_channel(self.password + '\n')
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel('\n')
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

        # If no delay_factor use 1 for default value
        delay_factor = kwargs.get('delay_factor', 1)
        kwargs['delay_factor'] = self.select_delay_factor(delay_factor)
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
                time.sleep(kwargs['delay_factor'] * 30)
                not_done = True
                i = 1
                while not_done and i <= 150:
                    time.sleep(kwargs['delay_factor'] * 3)
                    i += 1
                    new_data = ""
                    new_data = self.read_channel()
                    if new_data:
                        output += new_data
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

    def check_config_mode(self, check_string='config', pattern=''):
        """Checks if the device is in configuration mode or not."""
        if not pattern:
            pattern = self.base_prompt
        return super(CiscoWlcSSH, self).check_config_mode(check_string, pattern)

    def config_mode(self, config_command='config', pattern=''):
        """Enter into config_mode."""
        if not pattern:
            pattern = self.base_prompt
        return super(CiscoWlcSSH, self).config_mode(config_command, pattern)

    def exit_config_mode(self, exit_config='exit', pattern=''):
        """Exit config_mode."""
        if not pattern:
            pattern = self.base_prompt
        return super(CiscoWlcSSH, self).exit_config_mode(exit_config, pattern)

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Does not automatically exit/enter configuration mode.
        """
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ''
        if not hasattr(config_commands, '__iter__'):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        for cmd in config_commands:
            self.write_channel(self.normalize_cmd(cmd))
            time.sleep(delay_factor * .5)

        # Gather output
        output = self._read_channel_timing(delay_factor=delay_factor, max_loops=max_loops)
        output = self._sanitize_output(output)
        if debug:
            print(output)
        return output
