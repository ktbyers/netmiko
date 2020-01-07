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
        cmd = f"{self.RETURN}set cli mode -page OFF{self.RETURN}"
        self.disable_paging(command=cmd)
        time.sleep(1 * delay_factor)
        self.set_base_prompt()
        time.sleep(0.3 * delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self, pri_prompt_terminator="#", alt_prompt_terminator=">", delay_factor=1
    ):
        """Sets self.base_prompt.

        Netscaler has '>' for the prompt.
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")

        prompt = prompt.strip()
        if len(prompt) == 1:
            self.base_prompt = prompt
        else:
            # Strip off trailing terminator
            self.base_prompt = prompt[:-1]
        return self.base_prompt

    def check_config_mode(self):
        """Netscaler devices do not have a config mode."""
        return False

    def config_mode(self):
        """Netscaler devices do not have a config mode."""
        return ""

    def exit_config_mode(self):
        """Netscaler devices do not have a config mode."""
        return ""

    def strip_prompt(self, a_string):
        """ Strip 'Done' from command output """
        output = super().strip_prompt(a_string)
        lines = output.split(self.RESPONSE_RETURN)
        if "Done" in lines[-1]:
            return self.RESPONSE_RETURN.join(lines[:-1])
        else:
            return output
