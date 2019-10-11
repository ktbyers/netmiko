from netmiko.cisco_base_connection import CiscoSSHConnection
import re


class EndaceSSH(CiscoSSHConnection):
    def disable_paging(self, command="no cli session paging enable", delay_factor=1):
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def enable(self, cmd="enable", pattern="", re_flags=re.IGNORECASE):
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def check_config_mode(self, check_string="(config) #"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="conf t", pattern=""):
        output = ""
        if not self.check_config_mode():
            output = self.send_command_timing(
                config_command, strip_command=False, strip_prompt=False
            )
            if "to enter configuration mode anyway" in output:
                output += self.send_command_timing(
                    "YES", strip_command=False, strip_prompt=False
                )
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode")
        return output

    def exit_config_mode(self, exit_config="exit", pattern="#"):
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self, cmd="configuration write", confirm=False, confirm_response=""
    ):
        self.enable()
        self.config_mode()
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
