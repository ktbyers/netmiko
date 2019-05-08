from netmiko.cisco_base_connection import CiscoSSHConnection


class IonBase(CiscoSSHConnection):
    def establish_connection(self):
        super(IonBase, self).establish_connection(width=100, height=1000)

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        # Clear the read buffer
        self.write_channel(self.RETURN)
        self.set_base_prompt(delay_factor=5)

    def disable_paging(self):
        """Cloud Genix ION sets terminal heigh in establish_connection"""
        return ""

    def find_prompt(self, delay_factor=1):
        prompt = super(IonBase, self).find_prompt()
        prompt = self.strip_backspaces(prompt).strip()
        return prompt

    def strip_command(self, command_string, output):
        output = super(IonBase, self).strip_command(command_string, output)
        # handle command_string being repainted - otherwise return normal output
        if len(output.split(command_string)) == 4:
            output = output.split(command_string)[3]
        return output

    def config_mode(self):
        """No configuration mode on ION SSH"""
        self._in_config_mode = True
        return ""

    def check_config_mode(self, check_string=""):
        """Checks whether in configuration mode. Returns a boolean."""
        return self._in_config_mode

    def exit_config_mode(self, exit_config="#"):
        """No configuration mode on ION SSH"""
        self._in_config_mode = False
        return ""

    def save_config(self, *args, **kwargs):
        """No save method on ION SSH"""
        pass


class IonSSH(IonBase):
    pass
