
import time
import re

from netmiko.cisco_base_connection import CiscoSSHConnection


class routerosSSH(CiscoSSHConnection):
    """MicroTik RouterOS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = '\r\n'
        
        return super(routerosSSH, self).__init__(**kwargs) 

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
#        self.base_prompt = r"\[.*?\] \>"
        self.base_prompt = r"\[.*?\]\s\>\s.*\[.*?\]\s\>\s"
        # Clear the read buffer
        self.write_channel(self.RETURN)
        self.set_base_prompt()

    def _modify_connection_params(self):
         self.username += "+cetw511h4098"

    def _enter_shell(self):
        """Already in shell."""
        return ""

    def _return_cli(self):
        """The shell is the CLI."""
        return ""

    def disable_paging(self):
        """Microtik does not have paging by default."""
        return ""

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on RouterOS"""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on RouterOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on RouterOS."""
        return ""

    def save_config(self, *args, **kwargs):
        """No save command, all configuration is atomic"""
        pass

#    def config_mode(self, config_command=""):
#        """No configuration mode on Microtik"""
#        return ""
#
#    def check_config_mode(self, check_string=">"):
#        """Checks whether in configuration mode. Returns a boolean."""
#        print (super(routerosSSH, self).check_config_mode(check_string=check_string))
#        return super(routerosSSH, self).check_config_mode(check_string=check_string)
#
#
#    def exit_config_mode(self, exit_config="exit"):
#        return self.exit_enable_mode(exit_command=exit_config)
#

    def config_mode(self, config_command=""):
        """No configuration mode on Extreme Exos."""
        return ""

    def check_config_mode(self, check_string=">"):
        """Checks whether in configuration mode. Returns a boolean."""
        return super(routerosSSH, self).check_config_mode(check_string=check_string)

    def exit_config_mode(self, exit_config=""):
        """No configuration mode on Extreme Exos."""
        return ""

    def strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output.
        MT adds some garbage trailing newlines, so 
        trim the last two lines from the output.

        :param a_string: Returned string from device
        :type a_string: str
        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-2]
        if self.base_prompt in last_line:
            return self.RESPONSE_RETURN.join(response_list[:-2])
        else:
            return a_string

    def strip_command(self, command_string, output):
        """
        Strip command_string from output string

        MT returns, the Command\nRouterpromptCommand\n\n
        start the defaut return at len(self.get_prompt())+2*len(command)+1

        :param command_string: The command string sent to the device
        :type command_string: str

        :param output: The returned output as a result of the command string sen
        :type output: str
        """
        command_length = len(self.find_prompt()) + 2*(len(command_string)) + 2
        print(output[command_length:])
        return output[command_length:]

