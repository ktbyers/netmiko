import time

from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.py23_compat import string_types


class CloudGenixIonSSH(CiscoSSHConnection):
    def establish_connection(self):
        super(CloudGenixIonSSH, self).establish_connection(width=100, height=1000)

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.write_channel(self.RETURN)
        self.set_base_prompt(delay_factor=5)

    def disable_paging(self):
        """Cloud Genix ION sets terminal height in establish_connection"""
        return ""

    def find_prompt(self, delay_factor=1):
        prompt = super(CloudGenixIonSSH, self).find_prompt()
        prompt = self.strip_backspaces(prompt).strip()
        return prompt

    def strip_command(self, command_string, output):
        output = super(CloudGenixIonSSH, self).strip_command(command_string, output)
        # command_string gets repainted potentially multiple times (grab everything after last one)
        output = output.split(command_string)[-1]
        return output

    def check_config_mode(self):
        """Devices do not have a config mode."""
        return False

    def config_mode(self):
        """Devices do not have a config mode."""
        return ""

    def exit_config_mode(self):
        """Devices do not have a config mode."""
        return ""

    def save_config(self, *args, **kwargs):
        """No save method on ION SSH"""
        pass

    def send_config_set(
        self,
        config_commands=None,
        exit_config_mode=False,
        delay_factor=1,
        max_loops=150,
        strip_prompt=False,
        strip_command=False,
        config_mode_command=None,
    ):
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ""
        elif isinstance(config_commands, string_types):
            config_commands = (config_commands,)

        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = ""
        for cmd in config_commands:
            output += self.send_command(cmd)
            if self.fast_cli:
                pass
            else:
                time.sleep(delay_factor * 0.05)

        output = self._sanitize_output(output)
        log.debug("{}".format(output))
        return output
