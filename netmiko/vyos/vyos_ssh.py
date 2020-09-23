import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class VyOSSSH(CiscoSSHConnection):
    """Implement methods for interacting with VyOS network devices."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="set terminal width 512", pattern="terminal")
        self.disable_paging(command="set terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on VyOS."""
        pass

    def check_config_mode(self, check_string="#"):
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="configure", pattern=r"[edit]"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="exit", pattern=r"exit"):
        """Exit configuration mode"""
        output = ""
        if self.check_config_mode():
            output = self.send_command_timing(
                exit_config, strip_prompt=False, strip_command=False
            )
            if "Cannot exit: configuration modified" in output:
                output += self.send_command_timing(
                    "exit discard", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(self, comment="", delay_factor=0.1):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        default:
           command_string = commit
        comment:
           command_string = commit comment <comment>

        """
        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = ["Failed to generate committed config", "Commit failed"]
        command_string = "commit"

        if comment:
            command_string += f' comment "{comment}"'

        output = self.config_mode()
        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
        )

        if any(x in output for x in error_marker):
            raise ValueError(f"Commit failed with following errors:\n\n{output}")
        return output

    def set_base_prompt(
        self, pri_prompt_terminator="$", alt_prompt_terminator="#", delay_factor=1
    ):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        # Set prompt to user@hostname (remove two additional characters)
        self.base_prompt = prompt[:-2].strip()
        return self.base_prompt

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        """Remain in configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
