import re

from netmiko.base_connection import BaseConnection


class EricssonIposSSH(BaseConnection):
    def check_enable_mode(self, check_string="#"):
        """
        Check if in enable mode. Return boolean.
        """
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable 15", pattern="ssword", re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """Disable paging default to a Cisco CLI method.

        :param command: Device command to disable pagination of output
        :type command: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def set_terminal_width(self, command="terminal width 512", delay_factor=1):
        """CLI terminals try to automatically adjust the line based on the width of the terminal.
        This causes the output to get distorted when accessed programmatically.

        Set terminal width to 511 which works on a broad set of devices.

        :param command: Command string to send to the device
        :type command: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        return super().set_terminal_width(command=command, delay_factor=delay_factor)

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        """Ericsson IPOS requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def exit_enable_mode(self, exit_command="disable"):
        """
        Exits enable (privileged exec) mode.
        """
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="configure", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """
        Exit from configuration mode.
        Ercisson output :
            end                   Commit configuration changes and return to exec mode
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, cmd="save config", confirm=True, confirm_response="yes"):
        """Saves configuration"""
        if confirm:
            output = self.send_command_timing(
                command_string=cmd, strip_prompt=False, strip_command=False
            )

            if confirm_response:
                output += self.send_command_timing(
                    confirm_response, strip_prompt=False, strip_command=False
                )
            else:
                output += self.send_command_timing(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            output = self.send_command(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
        return output

    def commit(self, confirm=False, confirm_delay=None, comment="", delay_factor=1):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        """

        delay_factor = self.select_delay_factor(delay_factor)

        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check"
            )

        command_string = "commit"
        commit_marker = "Transaction committed"
        if confirm:
            if confirm_delay:
                command_string = f"commit confirmed {confirm_delay}"
            else:
                command_string = "commit confirmed"
            commit_marker = "Commit confirmed ,it will be rolled back within"

        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += f" comment {comment}"

        output = self.config_mode()

        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
        )

        if commit_marker not in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        self.exit_config_mode()

        return output
