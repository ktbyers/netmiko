from netmiko.base_connection import BaseConnection
import time


class YamahaBase(BaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt(">")
        self.disable_paging(command="console lines infinity")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self, pri_prompt_terminator="#", alt_prompt_terminator=">", delay_factor=1
    ):
        """
        Yamaha has a prompt with a single character to eliminate the normal last
        character stripping and just use the last character.

        Use 'pri_prompt_terminator' to just declare which one should be used.
        """
        if pri_prompt_terminator == ">":
            self.base_prompt = ">"
        else:
            self.base_prompt = "#"
        return self.base_prompt

    def check_enable_mode(self, check_string="#"):
        return super.check_enable_mode()

    def enable(self, cmd="administrator", pattern=r"Password", **kwargs):
        output = super.enable(cmd=cmd, pattern=pattern, **kwargs)
        self.set_base_prompt("#")
        return output

    def exit_enable_mode(self, exit_command="exit"):
        output = super.exit_enable_mode(exit_command=exit_command)
        self.set_base_prompt(">")
        return output

    def check_config_mode(self, check_string="#", pattern=""):
        """Checks if the device is in administrator mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="administrator", pattern="ssword"):
        """Enter into administrator mode and configure device."""
        return self.enable()

    def exit_config_mode(self, exit_config="exit", pattern=">"):
        """
        No action taken. Call 'exit_enable_mode()' to explicitly exit Administration
        Level.
        """
        return ""

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """Saves Config."""
        if confirm is True:
            raise ValueError("Yamaha does not support save_config confirmation.")
        self.enable()
        # Some devices are slow so match on trailing-prompt if you can
        return self.send_command(command_string=cmd)


class YamahaSSH(YamahaBase):
    """Yamaha SSH driver."""

    pass


class YamahaTelnet(YamahaBase):
    """Yamaha Telnet driver."""

    pass
