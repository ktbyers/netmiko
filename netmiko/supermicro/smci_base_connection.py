"""SmciBaseConnection is netmiko SSH class for Supermicro blade/ToR switch platforms."""
from netmiko.base_connection import BaseConnection
from netmiko.ssh_exception import NetmikoAuthenticationException
import re
import time


class SmciBaseConnection(BaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.config_mode()
        self.disable_paging(command="set cli pagination off")
        self.set_terminal_width(command="terminal width 511")
        self.exit_config_mode()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string="#"):
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable(self, *args, **kwargs):
        """Supermicro switch does not support enable-mode command"""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """Supermicro switch does not support enable-mode command"""
        return ""

    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="config term", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def serial_login(
            self,
            pri_prompt_terminator=r"#\s*$",
            alt_prompt_terminator=r">\s*$",
            username_pattern=r"login",
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
            pri_prompt_terminator=r"#\s*$",
            alt_prompt_terminator=r">\s*$",
            username_pattern=r"login",
            pwd_pattern=r"assword",
            delay_factor=1,
            max_loops=20,
    ):
        """Telnet login. Can be username/password or just password."""
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

                self.write_channel(self.TELNET_RETURN)
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
        pass

    def save_config(
            self,
            cmd="write startup-config",
            confirm=False,
            confirm_response="[OK]",
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

    def commit(self, *args, **kwargs):
        """We don't have commit command."""
        return ""
