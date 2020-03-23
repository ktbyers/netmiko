from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from telnetlib import (IAC, DO, DONT, WILL, WONT, SB, SE, ECHO, SGA, NAWS)
from netmiko.ssh_exception import NetmikoAuthenticationException


class H3CBase(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        self.disable_paging("screen-length disable")
        self.config_mode()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command="system-view",  pattern=""):
        """Enter configuration mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="return", pattern=r">"):
        """Exit config mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string="]", pattern=""):
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def set_base_prompt(
        self, pri_prompt_terminator=">", alt_prompt_terminator="]", delay_factor=1
    ):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

        # Strip off leading character
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(self, cmd="system-view"):
        """enable mode on Comware is system-view."""
        return self.config_mode(config_command=cmd)

    def exit_enable_mode(self, exit_command="return"):
        """enable mode on Comware is system-view."""
        return self.exit_config_mode(exit_config=exit_command)

    def check_enable_mode(self, check_string="]"):
        """enable mode on Comware is system-view."""
        return self.check_config_mode(check_string=check_string)

    def save_config(self, cmd="save force"):
        """Saves Config."""
        output = self.send_command_timing(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        return output


class H3CSSH(H3CBase):
    pass


class H3CTelnet(H3CBase):

    @staticmethod
    def _process_option(telnet_sock, cmd, opt):
        """
        H3C need set window size to receive long commands.
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
                telnet_sock.sendall(IAC + SB + NAWS + b"\x01\xf4\x00\x32" + IAC + SE)  # Width:500, Weight:50
            else:
                telnet_sock.sendall(IAC + WONT + opt)

    def telnet_login(
        self,
        pri_prompt_terminator=r"]\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"([Ll]ogin\:|[Uu]sername\:)",
        pwd_pattern=r"[Pp]assword:",
        delay_factor=1,
        max_loops=20,
    ):
        """
        Override BaseConnection Telnet login. Can be username/password or just password.
        Cut 'self.write_channel(self.TELNET_RETURN)' in 'while'.
        H3C devices will disconnect if receives too much attempts for password.

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
