from __future__ import unicode_literals
import paramiko
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection

class FortinetSSH(CiscoSSHConnection):
    def _modify_connection_params(self):
        """Modify connection parameters prior to SSH connection."""
        paramiko.Transport._preferred_kex = (
            "diffie-hellman-group14-sha1",
            "diffie-hellman-group-exchange-sha1",
            "diffie-hellman-group-exchange-sha256",
            "diffie-hellman-group1-sha1",
        )

    def special_login_handler(self, delay_factor=1, count=10):
        """
        Handle Fortinet devices when they are configured with pre-login
        banner:
            FG621B # config system global
            FG621B (global) # set pre-login-banner enable
            FG621B (global) # end
        """
        pattern = '\(Press \'a\' to accept\):'
        
        def _increment_delay(main_delay, increment=1.1, maximum=8):
            """Increment sleep time to a maximum value."""
            main_delay = main_delay * increment
            if main_delay >= maximum:
                main_delay = maximum
            return main_delay

        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)
        main_delay = delay_factor * 0.1
        time.sleep(main_delay * 10)
        new_data = ""
        while i <= count:
            new_data += self._read_channel_timing()
            if new_data and pattern:
                if re.search(pattern, new_data):
                    break
            elif new_data:
                self.write_channel('a') # Send 'a' to accept banner
                break
            else:
                self.write_channel(self.RETURN)
            main_delay = _increment_delay(main_delay)
            time.sleep(main_delay)
            i += 1

        # check if data was ever present
        if new_data:
            return ""
        else:
            msg = f'Timeout waiting for pre-login banner'
            logger.info(msg)
            print(msg)


    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt(alt_prompt_terminator="$")
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, delay_factor=1):
        """Disable paging is only available with specific roles so it may fail."""
        check_command = "get system status | grep Virtual"
        output = self.send_command_timing(check_command)
        self.allow_disable_global = True
        self.vdoms = False
        self._output_mode = "more"

        if "Virtual domain configuration: enable" in output:
            self.vdoms = True
            vdom_additional_command = "config global"
            output = self.send_command_timing(vdom_additional_command, delay_factor=2)
            if "Command fail" in output:
                self.allow_disable_global = False
                self.remote_conn.close()
                self.establish_connection(width=100, height=1000)

        new_output = ""
        if self.allow_disable_global:
            self._retrieve_output_mode()
            disable_paging_commands = [
                "config system console",
                "set output standard",
                "end",
            ]
            # There is an extra 'end' required if in multi-vdoms are enabled
            if self.vdoms:
                disable_paging_commands.append("end")
            outputlist = [
                self.send_command_timing(command, delay_factor=2)
                for command in disable_paging_commands
            ]
            # Should test output is valid
            new_output = self.RETURN.join(outputlist)

        return output + new_output

    def _retrieve_output_mode(self):
        """Save the state of the output mode so it can be reset at the end of the session."""
        reg_mode = re.compile(r"output\s+:\s+(?P<mode>.*)\s+\n")
        output = self.send_command("get system console")
        result_mode_re = reg_mode.search(output)
        if result_mode_re:
            result_mode = result_mode_re.group("mode").strip()
            if result_mode in ["more", "standard"]:
                self._output_mode = result_mode

    def cleanup(self):
        """Re-enable paging globally."""
        if self.allow_disable_global:
            # Return paging state
            output_mode_cmd = "set output {}".format(self._output_mode)
            enable_paging_commands = ["config system console", output_mode_cmd, "end"]
            if self.vdoms:
                enable_paging_commands.insert(0, "config global")
            # Should test output is valid
            for command in enable_paging_commands:
                self.send_command_timing(command)

    def config_mode(self, config_command=""):
        """No config mode for Fortinet devices."""
        return ""

    def exit_config_mode(self, exit_config=""):
        """No config mode for Fortinet devices."""
        return ""

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
