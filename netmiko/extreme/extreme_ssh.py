"""Extreme support."""
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


QUESTIONS = {
    'save': 'Do you want to save configuration to',
}


class ExtremeSSH(CiscoSSHConnection):
    """Extreme support."""

    def session_preparation(self):
        """
        Extreme requires enable mode to disable paging.
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")

    def answer_questions(self, *args, **kwargs):
        """
        Send questions/answers with send_command_timing.
        """
        if len(args) >= 1:
            command_string = args[0]

        # handle commands which return a question
        output = self.send_command_timing(command_string)
        if QUESTIONS[command_string] in output:
            output += self.send_command_timing('yes')

        return output

    def send_command(self, *args, **kwargs):
        """
        Catch questions from the CLI.
        Handle prompt changes during command executions.
        """
        if len(args) >= 1:
            command_string = args[0]

        # command that prompt a question
        if command_string in QUESTIONS.keys():
            output = self.answer_questions(command_string)

        # all other commands
        else:
            # Turn off 'auto_find_prompt' which loses the striped base prompt
            kwargs.update({'auto_find_prompt': False})
            # refresh prompt, which could have been changed on previous command
            self.set_base_prompt()
            output = super(ExtremeSSH, self).send_command(*args, **kwargs)

        return output

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False):
        """
        Overwrite send_config_set to acomodate for commands which return a question
        and expect a reply.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ''
        if not hasattr(config_commands, '__iter__'):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = ''
        for command_string in config_commands:

            # command that prompt a question
            if command_string in QUESTIONS.keys():
                output += self.answer_questions(command_string)

            # all other commands
            else:
                self.write_channel(self.normalize_cmd(command_string))
                time.sleep(delay_factor * .5)

        # Gather output
        output += self._read_channel_timing(delay_factor=delay_factor, max_loops=max_loops)

        output = self._sanitize_output(output)
        return output

    def set_base_prompt(self, *args, **kwargs):
        """
        Extreme attaches an id to the prompt. The id increases with every command.
        It needs to br stripped off to match the prompt. Eg.

            testhost.1 #
            testhost.2 #
            testhost.3 #

        If new config is loaded and not saved yet, a '* ' prefix appears before the
        prompt, eg.

            * testhost.4 #
            * testhost.5 #
        """
        cur_base_prompt = super(ExtremeSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'[\*\s]{0,2}(.*)\.\d+', cur_base_prompt)
        if match:
            # strip off .\d from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def config_mode(self, config_command=''):
        """No configuration mode on Extreme."""
        return ''

    def check_config_mode(self, check_string='#'):
        """Checks whether in configuration mode. Returns a boolean."""
        return super(ExtremeSSH, self).check_config_mode(check_string=check_string)

    def exit_config_mode(self, exit_config=''):
        """No configuration mode on Extreme."""
        return ''
