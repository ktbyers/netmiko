"""Subclass specific to Cisco Viptela."""
import re
import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoViptelaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco Viptela."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="paginate false")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=")#", pattern="#"):
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def commit(self, confirm=False, confirm_response=""):
        cmd = "commit"
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def config_mode(self, config_command="conf terminal", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        return super().config_mode(config_command=config_command, pattern=pattern)

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def exit_config_mode(self, exit_config="end", pattern=r"#"):
        """
        Exit from configuration mode.

        Viptela might have the following in the output (if no 'commit()' occurred.

        Uncommitted changes found, commit them? [yes/no/CANCEL]
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            if not re.search(pattern, output, flags=re.M):
                uncommit_pattern = r"Uncommitted changes found"
                new_pattern = f"({pattern}|{uncommit_pattern})"
                output += self.read_until_pattern(pattern=new_pattern)
                # Do not save 'uncommited changes'
                if uncommit_pattern in output:
                    self.write_channel(self.normalize_cmd("no"))
                    output += self.read_until_pattern(pattern=pattern)

            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def save_config(self, cmd="commit", confirm=False, confirm_response=""):
        """Saves Config"""
        raise NotImplementedError
