import socket
import telnetlib
import re

import paramiko
import serial
from paramiko import SSHException

from netmiko.channel import Channel, SSHChannel, TelnetChannel, SerialChannel
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException
)


class CiscoS200Base(CiscoSSHConnection):
    """
    Support for Cisco SG200 series of devices.

    This connection class writes for low-cost switches SG200 series, in which there is no command
    ip ssh password-auth
    and username promted twice

    The switch does not support any SSH authentication methods.
    """


    def establish_connection(self, width: int = 511, height: int = 1000) -> None:
        """Establish SSH connection to the network device
        Timeout will generate a NetmikoTimeoutException
        Authentication failure will generate a NetmikoAuthenticationException
        :param width: Specified width of the VT100 terminal window (default: 511)
        :type width: int
        :param height: Specified height of the VT100 terminal window (default: 1000)
        :type height: int
        """
        self.channel: Channel
        if self.protocol == "telnet":
            self.remote_conn = telnetlib.Telnet(
                self.host, port=self.port, timeout=self.timeout
            )
            # Migrating communication to channel class
            self.channel = TelnetChannel(conn=self.remote_conn, encoding=self.encoding)
            self.telnet_login()
        elif self.protocol == "serial":
            self.remote_conn = serial.Serial(**self.serial_settings)
            self.channel = SerialChannel(conn=self.remote_conn, encoding=self.encoding)
            self.serial_login()
        elif self.protocol == "ssh":
            ssh_connect_params = self._connect_params_dict()
            self.remote_conn_pre: Optional[paramiko.SSHClient]
            self.remote_conn_pre = self._build_ssh_client()

            # initiate SSH connection
            try:
                '''
                Do not provide password to SSHClient.connect()
                SSHClient.connect() should fail with SSHException('No authentication methods available') - swallow that exception
                '''
                del ssh_connect_params['password']
                self.remote_conn_pre.connect(**ssh_connect_params)
            except socket.error as conn_error:
                self.paramiko_cleanup()
                msg = f"""TCP connection to device failed.
Common causes of this problem are:
1. Incorrect hostname or IP address.
2. Wrong TCP port.
3. Intermediate firewall blocking access.
Device settings: {self.device_type} {self.host}:{self.port}
"""

                # Handle DNS failures separately
                if "Name or service not known" in str(conn_error):
                    msg = (
                        f"DNS failure--the hostname you provided was not resolvable "
                        f"in DNS: {self.host}:{self.port}"
                    )

                msg = msg.lstrip()
                raise NetmikoTimeoutException(msg)
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                self.paramiko_cleanup()
                msg = f"""Authentication to device failed.
Common causes of this problem are:
1. Invalid username and password
2. Incorrect SSH-key file
3. Connecting to the wrong device
Device settings: {self.device_type} {self.host}:{self.port}
"""

                msg += self.RETURN + str(auth_err)
                raise NetmikoAuthenticationException(msg)
            except paramiko.ssh_exception.SSHException as e:
                
                # Swallow exception and continue with special_login_handler
                if  "No authentication methods available" in str(e):
                    self.remote_conn_pre.get_transport().auth_none(self.username)
                
                elif "No existing session" in str(e):
                    self.paramiko_cleanup()
                    msg = (
                        "Paramiko: 'No existing session' error: "
                        "try increasing 'conn_timeout' to 15 seconds or larger."
                    )
                    raise NetmikoTimeoutException(msg)
                else:
                    self.paramiko_cleanup()
                    msg = f"""
A paramiko SSHException occurred during connection creation:
{str(e)}
"""
                    raise NetmikoTimeoutException(msg)

            if self.verbose:
                print(f"SSH connection established to {self.host}:{self.port}")

            # Use invoke_shell to establish an 'interactive session'
            self.remote_conn = self.remote_conn_pre.invoke_shell(
                term="vt100", width=width, height=height
            )

            self.remote_conn.settimeout(self.blocking_timeout)
            if self.keepalive:
                assert isinstance(self.remote_conn.transport, paramiko.Transport)
                self.remote_conn.transport.set_keepalive(self.keepalive)

            # Migrating communication to channel class
            self.channel = SSHChannel(conn=self.remote_conn, encoding=self.encoding)

            self.special_login_handler()
            if self.verbose:
                print("Interactive SSH session established")

        return None

    prompt_pattern = r"(?m:[>#]\s*$)"  # force re.Multiline

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Cisco SG2xx presents with the following on login

        login as: user

        Welcome to Layer 2 Managed Switch

        Username: user
        Password:****
        """
        output = ""
        uname = "Username:"
        login = "login as"
        password = "ssword"
        pattern = rf"(?:{uname}|{login}|{password}|{self.prompt_pattern})"

        while True:
            new_data = self.read_until_pattern(pattern=pattern, read_timeout=25.0)
            output += new_data
            if re.search(self.prompt_pattern, new_data):
                return

            if uname in new_data or login in new_data:
                assert isinstance(self.username, str)
                self.write_channel(self.username + self.RETURN)
            elif password in new_data:
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
            else:
                msg = f"""
Failed to login to Cisco SG2xx.

Pattern not detected: {pattern}
output:

{output}

"""
                raise NetmikoAuthenticationException(msg)


    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        # Command not support in SG220
        #self.set_terminal_width(command="terminal width 511", pattern="terminal")
        #self.disable_paging(command="terminal datadump")

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = True,
        confirm_response: str = "Y",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CiscoS200SSH(CiscoS200Base):
    pass


class CiscoS200Telnet(CiscoS200Base):
    """
    Support for Cisco SG200 series of devices, with telnet.
    """

    pass