from __future__ import print_function
from __future__ import unicode_literals

import re

from netmiko.ssh_connection import SSHConnection


class CiscoXrSSH(SSHConnection):

    def commit(self):
        '''
        Commit the entered configuration.

        Raise an error and return the failure if the commit fails.

        Automatically enter and exit configuration mode.
        '''

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self.send_command('commit', strip_prompt=False, strip_command=False)

        if "Failed to commit" in output:
            fail_msg = self.send_command('show configuration failed',
                                         strip_prompt=False, strip_command=False)

            raise ValueError('Commit failed with the following errors:\n\n \
                        {fail_msg}'.format(fail_msg=fail_msg))

        output += self.exit_config_mode()
        return output


    def commit_new(self, confirm=False, confirm_delay=None, comment='', label='', delay_factor=10):
        """
        Commit the candidate configuration.

        default (no options):
            command_string = commit
        confirm and confirm_delay:
            command_string = commit confirmed <confirm_delay>
        label (which is a label name):
            command_string = commit label <label>
        comment:
            command_string = commit comment <comment>

        combinations
        label and confirm:
            command_string = commit label <label> confirmed <confirm_delay>
        label and comment:        
            command_string = commit label <label> comment <comment>
        label, confirm, and comment:
            command_string = commit label <label> comment <comment> confirmed <confirm_delay>
        comment and confirm:
            command_string = commit comment <comment> confirmed <confirm_delay>

        failed commit message:
        % Failed to commit one or more configuration items during a pseudo-atomic operation. All 
        changes made have been reverted. Please issue 'show configuration failed [inheritance]' from 
        this session to view the errors        

        Exit of configuration mode with pending changes will cause the changes to be discarded and
        an exception to be generated.
        """

        if confirm and not confirm_delay:
            raise ValueError("Invalid arguments supplied to commit-confirm but no confirm_delay")
        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to commit-confirm_delay but no confirm")

        # Select proper command string based on arguments provided
        command_string = 'commit'
        commit_marker = 'Failed to'
        if confirm:
            if confirm_delay:
                command_string = 'commit confirmed ' + str(confirm_delay)
            else:
                command_string = 'commit confirmed'
            commit_marker = 'commit confirmed will be automatically rolled back in'

        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = '"{0}"'.format(comment)

            command_string += ' comment ' + comment

        if and_quit:
            command_string += ' and-quit'

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self.send_command(command_string, strip_prompt=False, strip_command=False,
                                    delay_factor=delay_factor)
        if not commit_marker in output:
            raise ValueError("Commit failed with the following errors:\n\n{0}"
                             .format(output))

        return output


    def exit_config_mode(self, exit_config='end'):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''
        debug = False
        output = ''

        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if "Uncommitted changes found" in output:
                output += self.send_command('no\n', strip_prompt=False, strip_command=False)
            if debug:
                print(output)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")

        return output


    @staticmethod
    def normalize_linefeeds(a_string):
        '''
        Convert '\r\n','\r\r\n', '\n\r', or '\r' to '\n
        '''

        newline = re.compile(r'(\r\r\n|\r\n|\n\r|\r)')

        return newline.sub('\n', a_string)


