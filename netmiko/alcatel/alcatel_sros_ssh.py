"""Alcatel-Lucent SROS support."""
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class AlcatelSrosSSH(CiscoSSHConnection):
    """Alcatel-Lucent SROS support."""

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="environment no more")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"(.*)(>.*)*#", cur_base_prompt)
        if match:
            # strip off >... from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def enable(self, cmd="enable-admin", pattern="ssword", re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def check_enable_mode(self, check_string="CLI Already in admin mode"):
        """Check whether we are in enable-admin mode.
         SROS requires us to do this:
        *A:HOSTNAME# enable-admin
        MINOR: CLI Already in admin mode.
        *A:HOSTNAME#
        *A:HOSTNAME# enable-admin
        Password:
        MINOR: CLI Invalid password.
        *A:HOSTNAME#
        """
        output = self.send_command_timing("enable-admin")
        if re.search(r"ssword", output):
            # Just hit enter as we don't actually want to enter enable here
            self.write_channel(self.normalize_cmd(self.RETURN))
            self.read_until_prompt()
            return False
        elif check_string in output:
            return True
        raise ValueError("Unexpected response in check_enable_mode() method")

    def exit_enable_mode(self, exit_command=""):
        """No corresponding exit of enable mode on SROS."""
        pass

    def config_mode(self, config_command="configure", pattern="#"):
        """ Enter into configuration mode on SROS device."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="exit all", pattern="#"):
        """ Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string="config", pattern="#"):
        """ Checks if the device is in configuration mode or not. """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
