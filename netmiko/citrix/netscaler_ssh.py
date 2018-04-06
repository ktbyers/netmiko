import time

from netmiko.base_connection import BaseConnection


class NetscalerSSH(BaseConnection):
    """ Netscaler SSH class. """

    def session_preparation(self):
        """Prepare the session after the connection has been established."""

        # 0 will defer to the global delay factor
        delay_factor = self.select_delay_factor(delay_factor=0)
        self._test_channel_read()
        self.set_base_prompt()
        cmd = "{}set cli mode -page OFF{}".format(self.RETURN, self.RETURN)
        self.disable_paging(command=cmd)
        time.sleep(1 * delay_factor)
        self.set_base_prompt()
        time.sleep(.3 * delay_factor)
        self.clear_buffer()

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """Nothing to exit"""
        return super(NetscalerSSH, self).send_config_set(config_commands=config_commands,
                                                         exit_config_mode=False, **kwargs)

    def strip_prompt(self, a_string):
        """ Strip 'Done' from command output """
        output = super(NetscalerSSH, self).strip_prompt(a_string)
        lines = output.split(self.RESPONSE_RETURN)
        if "Done" in lines[-1]:
            return 'self.RESPONSE_RETURN'.join(lines[:-1])
        else:
            return output
