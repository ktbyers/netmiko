from netmiko.cisco_base_connection import CiscoSSHConnection


class MikrotikBase(CiscoSSHConnection):
    """Common Methods for Mikrotik RouterOS and SwitchOS"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"

        self._in_config_mode = False

        return super().__init__(**kwargs)

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # Clear the read buffer
        self.write_channel(self.RETURN)
        self.set_base_prompt()
        self.clear_buffer()

    def _modify_connection_params(self):
        """Append login options to username
        c: disable console colors
        e: enable dumb terminal mode
        t: disable auto detect terminal capabilities
        w511: set term width
        h4098: set term height
        """
        self.username += "+cetw511h4098"

    def disable_paging(self, *args, **kwargs):
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

    def config_mode(self):
        """No configuration mode on Microtik"""
        self._in_config_mode = True
        return ""

    def check_config_mode(self, check_string=""):
        """Checks whether in configuration mode. Returns a boolean."""
        return self._in_config_mode

    def exit_config_mode(self, exit_config=">"):
        """No configuration mode on Microtik"""
        self._in_config_mode = False
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
        command_length = len(self.find_prompt()) + 2 * (len(command_string)) + 2
        return output[command_length:]


class MikrotikRouterOsSSH(MikrotikBase):
    """Mikrotik RouterOS SSH driver."""

    pass


class MikrotikSwitchOsSSH(MikrotikBase):
    """Mikrotik SwitchOS SSH driver."""

    pass
