#!/usr/bin/env python
# CDOT = Centre for Development of Telematics, India
# CROS = CDOT Router OS
# Script: cros_ssh.py
# Author: Maloy Ghosh <mghosh@cdot.in>
#
# Purpose: Provide basic SSH connection to CROS based router products

from netmiko.cisco_base_connection import CiscoBaseConnection
import time


class CdotCrosSSH(CiscoBaseConnection):
    """Implement methods for interacting with CROS network devices."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self._disable_complete_on_space()
        self.disable_paging(command="screen-length 0")
        self.set_terminal_width(command="screen-width 511")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
        return

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        """CROS requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def check_config_mode(self, check_string=")#", pattern=r"[#\$]"):
        """Checks if device is in configuration mode"""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="config", pattern=""):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def commit(self, comment="", delay_factor=1, and_quit=True):
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

        command_string = "commit"
        commit_marker = ["Commit complete", "No modifications to commit"]

        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            command_string += f' comment "{comment}"'

        output = self.config_mode()
        output += self.send_command(
            command_string,
            strip_prompt=False,
            strip_command=True,
            delay_factor=delay_factor,
        )

        if not (any(x in output for x in commit_marker)):
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        if and_quit:
            self.exit_config_mode()
        return output

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on CROS."""
        return True

    def enable(self, *args, **kwargs):
        """No enable mode on CROS."""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on CROS."""
        return ""

    def _disable_complete_on_space(self):
        """
        CROS tries to auto complete commands when you type a "space" character.

        This is a bad idea for automation as what your program is sending no longer matches
        the command echo from the device. So we disable this behavior.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(delay_factor * 0.1)
        command = "complete-on-space false"
        self.write_channel(self.normalize_cmd(command))
        time.sleep(delay_factor * 0.1)
        output = self.read_channel()
        return output
