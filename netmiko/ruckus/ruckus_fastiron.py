from __future__ import unicode_literals
import re
import time
from telnetlib import DO, DONT, ECHO, IAC, WILL, WONT
from netmiko.cisco_base_connection import CiscoSSHConnection


class RuckusFastironBase(CiscoSSHConnection):
    """Ruckus FastIron aka ICX support."""

    def session_preparation(self):
        """FastIron requires to be enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(
        self, cmd="enable", pattern=r"(ssword|User Name)", re_flags=re.IGNORECASE
    ):
        """Enter enable mode.
        With RADIUS can prompt for User Name
        SSH@Lab-ICX7250>en
        User Name:service_netmiko
        Password:
        SSH@Lab-ICX7250#

        Enter enable mode.
        without RADIUS failed attempt
        SSH@Lab-ICX7450>en

        Password:
        Error - Incorrect username or password.
        """
        output = ""

        max_loop = 2  # Try only 2 times
        i = 0
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )

        if not self.check_enable_mode():
            while i < max_loop:

                new_output = ""
                self.write_channel(self.normalize_cmd(cmd))
                new_output = self.read_until_pattern(pattern=pattern, re_flags=re_flags)

                output += new_output

                if "User Name" in new_output:
                    self.write_channel(self.normalize_cmd(self.username))
                    new_output = self.read_until_prompt_or_pattern(
                        pattern=pattern, re_flags=re_flags
                    )
                    output += new_output

                    if "Error" in new_output:
                        self.write_channel(self.RETURN)
                        i += 1
                        continue

                if "ssword" in new_output:
                    self.write_channel(self.normalize_cmd(self.secret))

                    output += self.read_until_prompt_or_pattern(
                        pattern=pattern, re_flags=re_flags
                    )

                    if self.check_enable_mode():
                        return output

                time.sleep(self.global_delay_factor)
                i += 1

            if self.check_enable_mode():
                return output
            else:
                raise ValueError(msg)

    def save_config(self, cmd="write mem", confirm=False, confirm_response=""):
        """Saves configuration."""
        return super(RuckusFastironBase, self).save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class RuckusFastironTelnet(RuckusFastironBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super(RuckusFastironTelnet, self).__init__(*args, **kwargs)

    def _process_option(self, tsocket, command, option):
        """
        Ruckus FastIron/ICX does not always echo commands to output by default.
        If server expresses interest in 'ECHO' option, then reply back with 'DO
        ECHO'
        """
        if option == ECHO:
            tsocket.sendall(IAC + DO + ECHO)
        elif command in (DO, DONT):
            tsocket.sendall(IAC + WONT + option)
        elif command in (WILL, WONT):
            tsocket.sendall(IAC + DONT + option)

    def telnet_login(self, *args, **kwargs):
        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self._process_option)
        return super(RuckusFastironTelnet, self).telnet_login(*args, **kwargs)


class RuckusFastironSSH(RuckusFastironBase):
    pass
