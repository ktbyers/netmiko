import re
import time
import socket
from os import path
from typing import Optional

from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log
from netmiko.utilities import m_exec_time  # noqa
from netmiko.exceptions import ReadTimeout
from datetime import datetime

class HPProcurveBase(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        """
        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        # Procurve over SSH uses 'Press any key to continue'
        print(datetime.now())
        data = self._test_channel_read(pattern=r"(any key to continue|[>#])")
        if "any key to continue" in data:
            self.write_channel(self.RETURN)
            self._test_channel_read(pattern=r"[>#]")
        print(datetime.now())

        self.set_base_prompt()
        print(datetime.now())
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        print(datetime.now())
        command = self.RETURN + "no page"
        self.disable_paging(command=command)
        print(datetime.now())

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "password",
        enable_pattern: Optional[str] = None,
        re_flags: int = re.IGNORECASE,
        default_username: str = "manager",
    ) -> str:
        """Enter enable mode"""

        if self.check_enable_mode():
            return ""

        output = ""
        username_pattern = r"(username|login|user name)"
        pwd_pattern = pattern
        prompt_pattern = r"[>#]"
        full_pattern = rf"(username|login|user name|{pwd_pattern}|{prompt_pattern})"

        # Send the enable command
        self.write_channel(cmd + self.RETURN)
        new_output = self.read_until_pattern(
            full_pattern, read_timeout=15, re_flags=re_flags
        )

        # Send the username
        if re.search(username_pattern, new_output, flags=re_flags):
            output += new_output
            self.write_channel(default_username + self.RETURN)
            full_pattern = rf"{pwd_pattern}|{prompt_pattern})"
            new_output = self.read_until_pattern(
                full_pattern, read_timeout=15, re_flags=re_flags
            )

        # Send the password
        if re.search(pwd_pattern, new_output, flags=re_flags):
            output += new_output
            self.write_channel(self.secret + self.RETURN)
            new_output = self.read_until_pattern(
                prompt_pattern, read_timeout=15, re_flags=re_flags
            )

        output += new_output
        log.debug(f"{output}")
        self.clear_buffer()
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        if not self.check_enable_mode():
            raise ValueError(msg)
        return output

    @m_exec_time
    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""

        print("cleanup")
        print(datetime.now())
        # Exit configuration mode.
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        print(datetime.now())

        # Terminate SSH/telnet session
        self.write_channel(command + self.RETURN)

        output = ""
        for _ in range(10):

            # The connection might be dead here.
            try:
                # "Do you want to log out" 
                # "Do you want to save the current"
                pattern=r"Do you want.*"
                new_output = self.read_until_pattern(pattern, read_timeout=1.5)
                print(f"new_output: {new_output}")
                output += new_output

                if "Do you want to log out" in new_output:
                    self.write_channel("y" + self.RETURN)
                    break
                elif "Do you want to save the current" in new_output:
                    # Don't automatically save the config (user's responsibility)
                    self.write_channel("n" + self.RETURN)
            except socket.error:
                print("Socket Error")
                break
            except ReadTimeout:
                print("ReadTimeout")
                break
            except Exception:
                print("Generic exception")
                break

            print(datetime.now())
            time.sleep(0.05)

        # Set outside of loop
        self._session_log_fin = True
        print(datetime.now())
        print("cleanup end")

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class HPProcurveSSH(HPProcurveBase):
    def _build_ssh_client(self) -> SSHClient:
        """Allow passwordless authentication for HP devices being provisioned."""

        # Create instance of SSHClient object. If no SSH keys and no password, then use noauth
        print("_build_ssh_client")
        print(datetime.now())
        remote_conn_pre: SSHClient
        if not self.use_keys and not self.password:
            remote_conn_pre = SSHClient_noauth()
        else:
            remote_conn_pre = SSHClient()
        print(datetime.now())

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        print(datetime.now())
        print("_build_ssh_client end")
        return remote_conn_pre


class HPProcurveTelnet(HPProcurveBase):
    def telnet_login(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        username_pattern: str = r"Login Name:",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 60,
    ) -> str:
        """Telnet login: can be username/password or just password."""
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
