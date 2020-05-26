from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, ECHO, SGA, NAWS
from netmiko.ssh_exception import NetmikoAuthenticationException


class RaisecomBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging("terminal page-break disable")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=")#", pattern="#"):
        """
        Checks if the device is in configuration mode or not.

        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)


class RaisecomSSH(RaisecomBase):
    pass


class RaisecomTelnet(RaisecomBase):
    @staticmethod
    def _process_option(telnet_sock, cmd, opt):
        """
        enable ECHO, SGA, set window size to [500, 50]

        """
        if cmd == WILL:
            if opt in [ECHO, SGA]:
                # reply DO ECHO / DO SGA
                telnet_sock.sendall(IAC + DO + opt)
            else:
                telnet_sock.sendall(IAC + DONT + opt)
        elif cmd == DO:
            if opt == NAWS:
                # negotiate about window size
                telnet_sock.sendall(IAC + WILL + opt)
                # Width:500, Weight:50
                telnet_sock.sendall(IAC + SB + NAWS + b"\x01\xf4\x00\x32" + IAC + SE)
            else:
                telnet_sock.sendall(IAC + WONT + opt)

    def telnet_login(
        self,
        pri_prompt_terminator=r"#\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"([Ll]ogin\:|[Uu]sername\:)",
        pwd_pattern=r"[Pp]assword:",
        delay_factor=1,
        max_loops=20,
    ):
        """
        Override BaseConnection Telnet login. Can be username/password or just password.
        Cut 'self.write_channel(self.TELNET_RETURN)' in 'while'.
        Raisecom devices will disconnect if receives too much attempts for password.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt
        :type pri_prompt_terminator: str

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt
        :type alt_prompt_terminator: str

        :param username_pattern: Pattern used to identify the username prompt
        :type username_pattern: str

        :param pwd_pattern: password
        :type pwd_pattern: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        :param max_loops: Controls the wait time in conjunction with the delay_factor
        (default: 20)
        """
        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self._process_option)
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output, flags=re.I):
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output, flags=re.I):
                    self.write_channel(self.password + self.TELNET_RETURN)
                    time.sleep(0.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if re.search(
                        pri_prompt_terminator, output, flags=re.M
                    ) or re.search(alt_prompt_terminator, output, flags=re.M):
                        return return_msg

                # Check if proper data received
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                    alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                time.sleep(0.5 * delay_factor)
                i += 1
            except EOFError:
                self.remote_conn.close()
                msg = f"Login failed: {self.host}"
                raise NetmikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        msg = f"Login failed: {self.host}"
        self.remote_conn.close()
        raise NetmikoAuthenticationException(msg)
