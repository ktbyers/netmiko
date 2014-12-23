import time
import re

from netmiko.base_connection import BaseSSHConnection

class JuniperSSH(BaseSSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''

        self.cli_mode()
        self.disable_paging(command="set cli screen-length 0\n")
        self.find_prompt()


    def cli_mode(self, delay_factor=1):
        '''
        Enter Juniper cli
        '''
        self.clear_buffer()
        self.remote_conn.send("cli\n")
        time.sleep(1*delay_factor)
        self.clear_buffer()

        return None


    def config_mode(self):
        '''
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''

        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if not '[edit' in output:
            output += self.send_command('configure\n')
            if 'unknown command' in output:
                raise ValueError("Failed to enter configuration mode")
            if not '[edit' in output:
                raise ValueError("Failed to enter configuration mode")

        return output


    def exit_config_mode(self):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''

        # only new_output is returned if 'exit' is executed
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if '[edit' in output:
            new_output = self.send_command('exit configuration-mode', strip_prompt=False, strip_command=False)
            if '[edit' in new_output:
                raise ValueError("Failed to exit configuration mode")
            return new_output

        return output


    def commit(self, delay_factor=10):
        '''
        Commit the entered configuration. Raise an error
        and return the failure if the commit fails.

        Juniper commit command must be in config mode
        '''

        # Enter config mode (if necessary)
        output = self.config_mode()

        output += self.send_command('commit',
                    strip_prompt=False, strip_command=False, delay_factor=delay_factor)

        if not "commit complete" in output:
            raise ValueError('Commit failed with the following errors:\n\n \
                        {0}'.format(output) )

        output += self.exit_config_mode()
        return output


    def strip_prompt(self, *args, **kwargs):
        '''
        Strip the trailing router prompt from the output
        '''

        # Call the parent strip_prompt method
        a_string = super(JuniperSSH, self).strip_prompt(*args, **kwargs)

        # Call additional method to strip some context items
        return self.strip_context_items(a_string)


    def strip_context_items(self, a_string):
        '''
        Juniper will also put a configuration context:
        [edit]

        and a virtual chassis context:
        {master:0}, {backup:1}
        '''

        strings_to_strip = [
            r'\[edit.*\]',
            r'\{master:.*\}',
            r'\{backup:.*\}',
            r'\{line.*\}',
        ]

        response_list = a_string.split('\n') 
        last_line = response_list[-1]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return "\n".join(response_list[:-1])

        return a_string
