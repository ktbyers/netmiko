from netmiko.base_connection import BaseConnection

class NetscalerSSH(BaseConnection):
    """ Netscaler SSH class. """

    def session_preparation(self):
        """Prepare the session after the connection has been established."""

        # 0 will defer to the global delay factor
        delay_factor = self.select_delay_factor(delay_factor=0)
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="\nset cli mode -page OFF\n")
        time.sleep(1 * delay_factor)
        self.set_base_prompt()

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """ Nothing to exit"""
        return super(NetscalerSSH, self).send_config_set(config_commands=config_commands,
                                                         exit_config_mode=False, **kwargs)

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove '\r's in the text."""
        # Done appears post-commands at times, blow it away.
        newline = re.compile(r'(\r\n|\r\n\r\n|\r\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)

    def strip_prompt(self, a_string):
        """ Strip 'Done' from command output """
        output = super(NetscalerSSH, self).strip_prompt(a_string)
        lines = output.split('\n')
        if "Done" in lines[-1]:
            return '\n'.join(lines[:-1])
        else:
            return output
