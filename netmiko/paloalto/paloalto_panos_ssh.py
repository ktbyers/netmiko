from __future__ import unicode_literals
import re

from netmiko.ssh_connection import BaseSSHConnection


class PaloAltoPanosSSH(BaseSSHConnection):
    '''
    Implement methods for interacting with PaloAlto devices.

    Subclass of SSHConnection.  Disables `enable()` and `check_enable_mode()`
    methods.  Overrides several methods for PaloAlto-specific compatibility.
    '''
    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self.set_base_prompt(delay_factor=3)
        self.disable_paging(command="set cli pager off\n")

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def check_config_mode(self, check_string=']'):
        """Checks if the device is in configuration mode or not."""
        return super(PaloAltoPanosSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(PaloAltoPanosSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='exit'):
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(self, force=False, partial=False, device_and_network=False,
               policy_and_objects=False, vsys='', no_vsys=False, delay_factor=.1):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        (device_and_network or policy_and_objects or vsys or
                no_vsys) and not partial:
            Exception
        """
        delay_factor = self.select_delay_factor(delay_factor)

        if ((device_and_network or policy_and_objects or vsys or
                no_vsys) and not partial):
            raise ValueError("'partial' must be True when using "
                             "device_and_network or policy_and_objects "
                             "or vsys or no_vsys.")

        # Select proper command string based on arguments provided
        command_string = 'commit'
        commit_marker = 'configuration committed successfully'
        if force:
            command_string += ' force'
        if partial:
            command_string += ' partial'
            if vsys:
                command_string += ' {0}'.format(vsys)
            if device_and_network:
                command_string += ' device-and-network'
            if policy_and_objects:
                command_string += ' device-and-network'
            if no_vsys:
                command_string += ' no-vsys'
            command_string += ' excluded'

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self.send_command_expect(command_string, strip_prompt=False,
                                           strip_command=False, expect_string='100%')

        if commit_marker not in output.lower():
            raise ValueError("Commit failed with the following errors:\n\n{0}"
                             .format(output))
        return output

    def strip_command(self, command_string, output):
        """
        Strip command_string from output string
        """
        output_list = output.split(command_string)
        return '\n'.join(output_list)

    def strip_prompt(self, a_string):
        '''
        Strip the trailing router prompt from the output
        '''
        response_list = a_string.split('\n')
        new_response_list = []
        for line in response_list:
            if self.base_prompt not in line:
                new_response_list.append(line)

        output = '\n'.join(new_response_list)
        return self.strip_context_items(output)

    @staticmethod
    def strip_context_items(a_string):
        """Strip PaloAlto-specific output.

        PaloAlto will also put a configuration context:
        [edit]

        This method removes those lines.
        """
        strings_to_strip = [
            r'\[edit.*\]',
        ]

        response_list = a_string.split('\n')
        last_line = response_list[-1]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return "\n".join(response_list[:-1])

        return a_string

    def send_command_expect(self, *args, **kwargs):
        """Palo Alto requires an extra delay"""
        kwargs['delay_factor'] = kwargs.get('delay_factor', .5)
        return super(PaloAltoPanosSSH, self).send_command_expect(*args, **kwargs)
