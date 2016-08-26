from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_connection import BaseSSHConnection


class VyOSSSH(BaseSSHConnection):
    """Implement methods for interacting with VyOS network devices."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging(command="set terminal length 0\n")

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def check_config_mode(self, check_string='#'):
        """Checks if the device is in configuration mode"""
        return super(VyOSSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='configure', pattern='[edit]'):
        """Enter configuration mode."""
        return super(VyOSSSH, self).config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config='exit', pattern='exit'):
        """Exit configuration mode"""
        output = ""
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if 'Cannot exit: configuration modified' in output:
                # insert delay?
                output += self.send_command('exit discard', strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(self, comment='', delay_factor=.1):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        default:
           command_string = commit
        comment:
           command_string = commit comment <comment>

        """
        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = 'Failed to generate committed config'
        command_string = 'commit'

        if comment:
            command_string += ' comment "{}"'.format(comment)

        output = self.config_mode()
        output += self.send_command_expect(command_string, strip_prompt=False,
                                           strip_command=False, delay_factor=delay_factor)

        if error_marker in output:
            raise ValueError('Commit failed with following errors:\n\n{}'.format(output))
        return output

    def set_base_prompt(self, pri_prompt_terminator='$', alt_prompt_terminator='#',
                        delay_factor=.5):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        debug = False
        if debug:
            print("In set_base_prompt")

        delay_factor = self.select_delay_factor(delay_factor)
        prompt = self.find_prompt(delay_factor=delay_factor)

        # If multiple lines in the output take the last line
        prompt = prompt.split('\n')[-1].strip()

        # Check that ends with a valid terminator character
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("Router prompt not found: {0}".format(prompt))

        # Set prompt to user@hostname
        self.base_prompt = prompt[:-3].strip()
        if debug:
            print("prompt: {}".format(self.base_prompt))
        return self.base_prompt
