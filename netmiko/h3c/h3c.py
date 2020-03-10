from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from netmiko import log
from telnetlib import (IAC, DO, DONT, WILL, WONT, SB, SE, ECHO, SGA, NAWS)


class H3CBase(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        self.disable_paging("screen-length disable")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command="system-view"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="return", pattern=r">"):
        """Exit config mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string="]"):
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string)

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

    def save_config(self, cmd="save force", confirm=False, confirm_response=""):
        """Save Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class H3CSSH(H3CBase):
    pass


class H3CTelnet(H3CBase):

    @staticmethod
    def _process_option(telnet_sock, cmd, opt):
        """
        ZTE need manually reply DO ECHO to enable echo command.
        enable ECHO, SGA, set window size to [500, 50]

        """
        if cmd == WILL:
            if opt == (ECHO or SGA):
                # reply DO ECHO / DO SGA
                telnet_sock.sendall(IAC + DO + opt)
            else:
                telnet_sock.sendall(IAC + DONT + opt)
        elif cmd == DO:
            if opt == NAWS:
                # negotiate about window size
                telnet_sock.sendall(IAC + WILL + opt)
                telnet_sock.sendall(IAC + SB + NAWS + b"\x01\xf4\x00\x32" + IAC + SE)  # Width:500, Weight:50
                # telnet_sock.sendall(
                # IAC + SB + NAWS + (500).to_bytes(2, byteorder="big") + (50).to_bytes(2, byteorder="big") + IAC + SE)
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
