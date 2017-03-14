from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class FortinetSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt(alt_prompt_terminator='$')
        self.disable_paging()

    def disable_paging(self, delay_factor=1):
        """Disable paging is only available with specific roles so it may fail."""
        check_command = "get system status | grep Virtual\n"
        output = self.send_command_timing(check_command)
        self.allow_disable_global = True
        self.vdoms = False

        if "Virtual domain configuration: enable" in output:
            self.vdoms = True
            vdom_additional_command = "config global"
            output = self.send_command_timing(vdom_additional_command, delay_factor=2)
            if "Command fail" in output:
                self.allow_disable_global = False
                self.remote_conn.close()
                self.establish_connection(width=100, height=1000)

        new_output = ''
        if self.allow_disable_global:
            disable_paging_commands = ["config system console", "set output standard", "end"]
            # There is an extra 'end' required if in multi-vdoms are enabled
            if self.vdoms:
                disable_paging_commands.append("end")
            outputlist = [self.send_command_timing(command, delay_factor=2)
                          for command in disable_paging_commands]
            # Should test output is valid
            new_output = "\n".join(outputlist)

        return output + new_output

    def cleanup(self):
        """Re-enable paging globally."""
        if self.allow_disable_global:
            enable_paging_commands = ["config system console", "set output more", "end"]
            if self.vdoms:
                enable_paging_commands.insert(0, "config global")
            # Should test output is valid
            for command in enable_paging_commands:
                self.send_command_timing(command)

    def config_mode(self, config_command=''):
        """No config mode for Fortinet devices."""
        return ''

    def exit_config_mode(self, exit_config=''):
        """No config mode for Fortinet devices."""
        return ''
