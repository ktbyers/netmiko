from netmiko.cisco_base_connection import CiscoSSHConnection


class CloudGenixIonSSH(CiscoSSHConnection):
    def establish_connection(self):
        super().establish_connection(width=100, height=1000)

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.write_channel(self.RETURN)
        self.set_base_prompt(delay_factor=5)

    def disable_paging(self, *args, **kwargs):
        """Cloud Genix ION sets terminal height in establish_connection"""
        return ""

    def find_prompt(self, delay_factor=1):
        prompt = super().find_prompt(delay_factor=delay_factor)
        prompt = self.strip_backspaces(prompt).strip()
        return prompt

    def strip_command(self, command_string, output):
        output = super().strip_command(command_string, output)
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

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )
