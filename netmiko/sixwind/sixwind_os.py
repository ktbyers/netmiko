import time
from netmiko.cisco_base_connection import CiscoBaseConnection


class SixwindOSBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, *args, **kwargs):
        """6WIND requires no-pager at the end of command, not implemented at this time."""
        pass

    def set_base_prompt(
        self, pri_prompt_terminator=">", alt_prompt_terminator="#", delay_factor=1
    ):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""

        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def config_mode(self, config_command="edit running", pattern=""):
        """Enter configuration mode."""

        return super().config_mode(config_command=config_command, pattern=pattern)

    def commit(self, comment="", delay_factor=1):
        """
        Commit the candidate configuration.

        Raise an error and return the failure if the commit fails.
        """

        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = "Failed to generate committed config"
        command_string = "commit"

        output = self.config_mode()
        output += self.send_command(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
            expect_string=r"#",
        )
        output += self.exit_config_mode()

        if error_marker in output:
            raise ValueError(f"Commit failed with following errors:\n\n{output}")

        return output

    def exit_config_mode(self, exit_config="exit", pattern=r">"):
        """Exit configuration mode."""

        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string="#", pattern=""):
        """Checks whether in configuration mode. Returns a boolean."""

        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self, cmd="copy running startup", confirm=True, confirm_response="y"
    ):
        """Save Config for 6WIND"""

        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def check_enable_mode(self, *args, **kwargs):
        """6WIND has no enable mode."""

        pass

    def enable(self, *args, **kwargs):
        """6WIND has no enable mode."""

        pass

    def exit_enable_mode(self, *args, **kwargs):
        """6WIND has no enable mode."""

        pass


class SixwindOSSSH(SixwindOSBase):

    pass
