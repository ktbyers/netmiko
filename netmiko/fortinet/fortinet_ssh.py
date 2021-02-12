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

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        output = ""

        # If "set post-login-banner enable" is set it will require you to press 'a'
        # to accept the banner before you login. This will accept if it occurs
        count = 1
        while count <= 30:
            output += self.read_channel()
            if "to accept" in output:
                self.write_channel("a\r")
                break
            else:
                time.sleep(0.33 * delay_factor)
            count += 1

        self._test_channel_read()
        self.set_base_prompt(alt_prompt_terminator="$")
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, delay_factor=1, **kwargs):
        """Disable paging is only available with specific roles so it may fail."""
        check_command = "get system status | grep Virtual"
        output = self.send_command_timing(check_command)
        self.allow_disable_global = True
        self.vdoms = False
        self._output_mode = "more"

        if re.search(r"Virtual domain configuration: (multiple|enable)", output):
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

    def cleanup(self, command="exit"):
        """Re-enable paging globally."""
        if self.allow_disable_global:
            # Return paging state
            output_mode_cmd = f"set output {self._output_mode}"
            enable_paging_commands = ["config system console", output_mode_cmd, "end"]
            if self.vdoms:
                enable_paging_commands.insert(0, "config global")
            # Should test output is valid
            for command in enable_paging_commands:
                self.send_command_timing(command)
        return super().cleanup(command=command)

    def check_config_mode(self, check_string=") #", pattern=""):
        """
        #Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="", pattern="", re_flags=0):
        """
        #Enter into configuration mode on remote device.
        #Several commands available only in config global mode or config vdom mode
        """

        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def config_mode_vdom(self, vdom_name="", new_vdom=False, pattern="", re_flags=0):
        """
        Function That will allow the user to enter in config vdom mode.
        This function will control if the VDOM exist or not if the new_VDOM is not changed to True
        Args:
            vdom_name (str, optional): [description]. Defaults to "".
                Supply here the name of the VDOM to edit
            new_vdom (bool, optional): [description]. Defaults to False.
                Change it to True to create a new VDOM
            pattern (str, optional): [description]. Defaults to "".
                The pattern used to identify that the output is complete
            re_flags (int, optional): [description]. Defaults to 0.
                regex flags used in conjunction with pattern to search for prompt
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        self.write_channel("config vdom\n")
        time.sleep(0.33 * delay_factor)
        if new_vdom:
            assert (
                vdom_name != ""
            ), "If you would like the creation of a new VDOM, please provide it"
            self.write_channel("edit " + vdom_name + "\n")
        else:
            assert vdom_name != "", "Supply a VDOM name to enter in config mode on it"
            self.write_channel("edit ?")
            time.sleep(0.33 * delay_factor)
            output = self.read_channel().splitlines()
            self.clear_buffer()
            vdom_list = output[2:-2]
            assert (
                vdom_name in vdom_list
            ), "VDOM Name not in the existing VDOMs. \
            If you expect a creation of it, change new_vdom to True "
            command = vdom_name + "\n"
            print(command)
            self.write_channel(command)
            time.sleep(0.33 * delay_factor)
            self.set_base_prompt()
            self.clear_buffer()

    def config_mode_global(
        self, config_command="config global", pattern="", re_flags=0
    ):
        self.config_mode(config_command, pattern, re_flags)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        # print(pattern)
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
