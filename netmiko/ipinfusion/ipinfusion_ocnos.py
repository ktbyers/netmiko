import time
from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE
from netmiko.cisco_base_connection import CiscoBaseConnection


class IpInfusionOcNOSBase(CiscoBaseConnection):
    """Common Methods for IP Infusion OcNOS support."""

    def __init__(self, *args, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd="write", confirm=False, confirm_response=""):
        """Saves Config Using write command"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class IpInfusionOcNOSSSH(IpInfusionOcNOSBase):
    """IP Infusion OcNOS SSH driver."""

    pass


class IpInfusionOcNOSTelnet(IpInfusionOcNOSBase):
    """IP Infusion OcNOS  Telnet driver."""

    def _process_option(self, tsocket, command, option):
        """
        For all telnet options, re-implement the default telnetlib behaviour
        and refuse to handle any options. If the server expresses interest in
        'terminal type' option, then reply back with 'xterm' terminal type.
        """
        if command == DO and option == TTYPE:
            tsocket.sendall(IAC + WILL + TTYPE)
            tsocket.sendall(IAC + SB + TTYPE + b"\0" + b"xterm" + IAC + SE)
        elif command in (DO, DONT):
            tsocket.sendall(IAC + WONT + option)
        elif command in (WILL, WONT):
            tsocket.sendall(IAC + DONT + option)

    def telnet_login(
        self,
        pri_prompt_terminator="#",
        alt_prompt_terminator=">",
        username_pattern=r"(?:user:|sername|login|user name)",
        pwd_pattern=r"assword:",
        delay_factor=1,
        max_loops=20,
    ):
        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self._process_option)
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
