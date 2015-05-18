from __future__ import unicode_literals
import re

from netmiko.ssh_connection import BaseSSHConnection

class JuniperSSH(BaseSSHConnection):
    """Implement methods for interacting with Juniper Networks devices.

    Subclass of SSHConnection.  Disables `enable()` and `check_enable_mode()`
    methods.  Overrides several methods for Juniper-specific compatibility.
    """

    def session_preparation(self):
        """Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self.disable_paging(command="set cli screen-length 0\n")
        self.set_base_prompt()


    def config_mode(self, config_command='configure'):
        '''
        Enter configuration mode.

        Checks to see if the session is already in configuration mode first.
        Raises `ValueError` if the session was unable to enter configuration
        mode.
        '''

        # Call parent class with specific command for entering config mode
        return super(JuniperSSH, self).config_mode(config_command=config_command)


    def exit_config_mode(self, exit_config='exit configuration-mode'):
        """Exit configuration mode.

        Check if we're in configuration mode.  If we are, exit configuration
        mode.  If we aren't, do nothing.
        """

        output = ""
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if 'Exit with uncommitted changes?' in output:
                output += self.send_command('yes', strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")

        return output


    def check_config_mode(self, check_string=']'):
        '''
        Checks if the device is in configuration mode or not

        Returns a boolean
        '''

        # Call parent class with Juniper check_string
        return super(JuniperSSH, self).check_config_mode(check_string=check_string)


    def commit(self, confirm=False, confirm_delay=None, check=False, comment='',
               and_quit=False, delay_factor=10):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        check and (confirm or confirm_dely or comment):
            Exception
        confirm_delay and no confirm:
            Exception
        confirm:
            confirm_delay option
            comment option
            command_string = commit confirmed or commit confirmed <confirm_delay>
        check:
            command_string = commit check

        """

        if check and (confirm or confirm_delay or comment):
            raise ValueError("Invalid arguments supplied with commit check")

        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to commit method both confirm and check")

        # Select proper command string based on arguments provided
        command_string = 'commit'
        commit_marker = 'commit complete'
        if check:
            command_string = 'commit check'
            commit_marker = 'configuration check succeeds'
        elif confirm:
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


    def strip_prompt(self, *args, **kwargs):
        """Strip the trailing router prompt from the output."""

        # Call the superclass strip_prompt method
        a_string = super(JuniperSSH, self).strip_prompt(*args, **kwargs)

        # Call additional method to strip some context items
        return self.strip_context_items(a_string)


    @staticmethod
    def strip_context_items(a_string):
        """Strip Juniper-specific output.

        Juniper will also put a configuration context:
        [edit]

        and various chassis contexts:
        {master:0}, {backup:1}

        This method removes those lines.
        """

        strings_to_strip = [
            r'\[edit.*\]',
            r'\{master:.*\}',
            r'\{backup:.*\}',
            r'\{line.*\}',
            r'\{primary.*\}',
            r'\{secondary.*\}',
        ]

        response_list = a_string.split('\n')
        last_line = response_list[-1]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return "\n".join(response_list[:-1])

        return a_string
