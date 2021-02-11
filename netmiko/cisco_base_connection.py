"""CiscoBaseConnection is netmiko SSH class for Cisco and Cisco-like platforms."""
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer
from netmiko.ssh_exception import NetmikoAuthenticationException
import re
import time


class CiscoBaseConnection(BaseConnection):
    """Base Class for cisco-like behavior."""

    def check_enable_mode(self, check_string="#"):
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd="enable",
        pattern="ssword",
        enable_pattern=None,
        re_flags=re.IGNORECASE,
    ):
        """Enter enable mode."""
        return super().enable(
            cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
        )

    def exit_enable_mode(self, exit_command="disable"):
        """Exits enable (privileged exec) mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="configure terminal", pattern="", re_flags=0):
        """
        Enter into configuration mode on remote device.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config="end", pattern=r"\#"):
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def serial_login(
        self,
        pri_prompt_terminator=r"\#\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"(?:user:|username|login)",
        pwd_pattern=r"assword",
        delay_factor=1,
        max_loops=20,
    ):
        self.write_channel(self.TELNET_RETURN)
        output = self.read_channel()
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return output
        else:
            return self.telnet_login(
                pri_prompt_terminator,
                alt_prompt_terminator,
                username_pattern,
                pwd_pattern,
                delay_factor,
                max_loops,
            )

    def telnet_login(
        self,
        pri_prompt_terminator=r"\#\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"(?:user:|username|login|user name)",
        pwd_pattern=r"assword",
        delay_factor=1,
        max_loops=20,
    ):
        """Telnet login. Can be username/password or just password."""
        delay_factor = self.select_delay_factor(delay_factor)

        # FIX: Cleanup in future versions of Netmiko
        if delay_factor < 1:
            if not self._legacy_mode and self.fast_cli:
                delay_factor = 1

        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        outer_loops = 3
        inner_loops = int(max_loops / outer_loops)
        i = 1
        for _ in range(outer_loops):
            while i <= inner_loops:
                try:
                    output = self.read_channel()
                    return_msg += output

                    # Search for username pattern / send username
                    if re.search(username_pattern, output, flags=re.I):
                        # Sometimes username/password must be terminated with "\r" and not "\r\n"
                        self.write_channel(self.username + "\r")
                        time.sleep(1 * delay_factor)
                        output = self.read_channel()
                        return_msg += output

                    # Search for password pattern / send password
                    if re.search(pwd_pattern, output, flags=re.I):
                        # Sometimes username/password must be terminated with "\r" and not "\r\n"
                        self.write_channel(self.password + "\r")
                        time.sleep(0.5 * delay_factor)
                        output = self.read_channel()
                        return_msg += output
                        if re.search(
                            pri_prompt_terminator, output, flags=re.M
                        ) or re.search(alt_prompt_terminator, output, flags=re.M):
                            return return_msg

                    # Support direct telnet through terminal server
                    if re.search(
                        r"initial configuration dialog\? \[yes/no\]: ", output
                    ):
                        self.write_channel("no" + self.TELNET_RETURN)
                        time.sleep(0.5 * delay_factor)
                        count = 0
                        while count < 15:
                            output = self.read_channel()
                            return_msg += output
                            if re.search(r"ress RETURN to get started", output):
                                output = ""
                                break
                            time.sleep(2 * delay_factor)
                            count += 1

                    # Check for device with no password configured
                    if re.search(r"assword required, but none set", output):
                        self.remote_conn.close()
                        msg = "Login failed - Password required, but none set: {}".format(
                            self.host
                        )
                        raise NetmikoAuthenticationException(msg)

                    # Check if proper data received
                    if re.search(
                        pri_prompt_terminator, output, flags=re.M
                    ) or re.search(alt_prompt_terminator, output, flags=re.M):
                        return return_msg

                    i += 1

                except EOFError:
                    self.remote_conn.close()
                    msg = f"Login failed: {self.host}"
                    raise NetmikoAuthenticationException(msg)

            # Try sending an <enter> to restart the login process
            self.write_channel(self.TELNET_RETURN)
            time.sleep(0.5 * delay_factor)
            i = 1

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        self.remote_conn.close()
        msg = f"Login failed: {self.host}"
        raise NetmikoAuthenticationException(msg)

    def cleanup(self, command="exit"):
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)

    def _autodetect_fs(self, cmd="dir", pattern=r"Directory of (.*)/"):
        """Autodetect the file system on the remote device. Used by SCP operations."""
        if not self.check_enable_mode():
            raise ValueError("Must be in enable mode to auto-detect the file-system.")
        output = self.send_command_expect(cmd)
        match = re.search(pattern, output)
        if match:
            file_system = match.group(1)
            # Test file_system
            cmd = f"dir {file_system}"
            output = self.send_command_expect(cmd)
            if "% Invalid" in output or "%Error:" in output:
                raise ValueError(
                    "An error occurred in dynamically determining remote file "
                    "system: {} {}".format(cmd, output)
                )
            else:
                return file_system

        raise ValueError(
            "An error occurred in dynamically determining remote file "
            "system: {} {}".format(cmd, output)
        )

    def save_config(
        self,
        cmd="copy running-config startup-config",
        confirm=False,
        confirm_response="",
    ):
        """Saves Config."""
        self.enable()
        if confirm:
            output = self.send_command_timing(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
            if confirm_response:
                output += self.send_command_timing(
                    confirm_response, strip_prompt=False, strip_command=False
                )
            else:
                # Send enter by default
                output += self.send_command_timing(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self.send_command(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
        return output


class CiscoSSHConnection(CiscoBaseConnection):
    pass


class CiscoFileTransfer(BaseFileTransfer):
    pass
