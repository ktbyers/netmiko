from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from netmiko import log
from telnetlib import (IAC, DO, DONT, WILL, WONT, SB, SE, ECHO, SGA, NAWS)


class YotcBase(CiscoBaseConnection):

    def send_command_more(self, *args, **kwargs):
        """
        yotc has no disable_paging command, need to handle it in show command.
        cisco_wlc_ssh.py has similar function: send_command_w_enter().
        :param args: same with send_command_timing()
        :param kwargs: same with send_command_timing()
        :return: output
        """
        prompt = self.find_prompt()
        more_str_re = f" --More-- \b\b\b\b\b\b\b\b\b\b          \b\b\b\b\b\b\b\b\b\b\n?|(\n?{re.escape(prompt)} ?\n?)+"
        buffer = self.send_command_timing(*args, cmd_echo=True, **kwargs)
        output = buffer
        while prompt not in buffer:
            buffer = self.send_command_timing("", strip_command=False, strip_prompt=False, cmd_echo=True)
            output += buffer
        output = re.sub(more_str_re, "", output)
        return output

    def session_preparation(self):
        """Prepare the session after the connection has been established."""

        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.config_mode()
        self.disable_paging("command max-lines 1000")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
    
    def check_config_mode(self, check_string=")#", pattern="#"):
        """
        Checks if the device is in configuration mode or not.

        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self,
        cmd="wr",
        confirm=True,
        confirm_response="y",
    ):
        """Saves Config."""
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)

    def cleanup(self):
        """
        no use exit command to disconnect
        :return:
        """
        pass


class YotcSSH(YotcBase):
    
    def special_login_handler(self, delay_factor=1):
        """yotc presents with the following on login

        Password: ***

        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "Password:" in output:
                    self.write_channel(self.secret + self.RETURN)
                    break
                time.sleep(delay_factor * 0.1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 0.1)
            i += 1


class YotcTelnet(YotcBase):

    def _process_option(self, telnet_sock, cmd, opt):
        """
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

    def telnet_login(self, *args, **kwargs):
        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self._process_option)
        return super().telnet_login(*args, **kwargs)
